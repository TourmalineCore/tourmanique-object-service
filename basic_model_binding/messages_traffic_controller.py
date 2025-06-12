import json
import logging
from threading import Thread

from basic_model_binding.message_packer import MessagePacker
from config.rabbitmq_config import rabbitmq_host, rabbitmq_username, rabbitmq_password, \
    rabbitmq_requests_exchange_name, rabbitmq_models_queues_dlx_name, \
    rabbitmq_models_retry_queue_dlx_name, rabbitmq_models_retry_queue_name, rabbitmq_models_retry_delay_ms, \
    rabbitmq_models_max_retry_number, rabbitmq_results_exchange_name, rabbitmq_port
from helpers.append_result_to_database import AppendResultsCommand
from model.object_model import ObjectModel

from pika import ConnectionParameters, PlainCredentials, BlockingConnection, BasicProperties
from pika.exceptions import ConnectionClosedByBroker, AMQPChannelError, AMQPConnectionError

from model.model_result_schema import ModelResultSchema
from config.model_config import processing_result_event_name

connection_parameters = ConnectionParameters(
    host=str(rabbitmq_host),
    port=rabbitmq_port,
    virtual_host='/',
    credentials=PlainCredentials(rabbitmq_username, rabbitmq_password),
)


class MessagesTrafficController(Thread):
    def __init__(self, model_type):
        self.model_type = model_type
        self.model_request_queue_name = f'{self.model_type}-queue'
        self.message_packer = MessagePacker(model_type)
        self.model = ObjectModel()
        self.connection = BlockingConnection(connection_parameters)

        super().__init__(target=self.start_listening_to_the_queue)

    def start_listening_to_the_queue(self):
        while True:
            try:
                logging.warning(f'Connecting to RabbitMQ: {rabbitmq_host}')

                channel = self.connection.channel()
                channel.exchange_declare(exchange=rabbitmq_requests_exchange_name,
                                         exchange_type='fanout')
                channel.exchange_declare(exchange=rabbitmq_models_queues_dlx_name,
                                         exchange_type='direct')
                channel.exchange_declare(exchange=rabbitmq_models_retry_queue_dlx_name,
                                         exchange_type='direct')
                channel.basic_qos(prefetch_count=1)

                channel.queue_declare(
                    queue=self.model_request_queue_name,
                    arguments={
                        "x-dead-letter-exchange": rabbitmq_models_queues_dlx_name,
                        'x-dead-letter-routing-key': self.model_request_queue_name
                    },
                    durable=True,
                    exclusive=False,
                    auto_delete=False,
                )

                channel.queue_declare(
                    queue=rabbitmq_models_retry_queue_name,
                    arguments={
                        'x-message-ttl': rabbitmq_models_retry_delay_ms,
                        "x-dead-letter-exchange": rabbitmq_models_retry_queue_dlx_name,
                    },
                    durable=True,
                    exclusive=False,
                    auto_delete=False,
                )

                channel.queue_bind(exchange=rabbitmq_requests_exchange_name, queue=self.model_request_queue_name)
                channel.queue_bind(exchange=rabbitmq_models_queues_dlx_name, queue=rabbitmq_models_retry_queue_name,
                                   routing_key=self.model_request_queue_name)
                channel.queue_bind(exchange=rabbitmq_models_retry_queue_dlx_name, queue=self.model_request_queue_name,
                                   routing_key=self.model_request_queue_name)

                channel.basic_consume(self.model_request_queue_name, self.request_message_processing)
                channel.start_consuming()
                logging.warning('Started consumption from the queue: {0}'.format(self.model_request_queue_name))

            except (ConnectionClosedByBroker, AMQPConnectionError):
                logging.warning('Connection was closed, retrying...')
                continue

            except AMQPChannelError as e:
                logging.error('Caught a channel error: {0}, stopping...'.format(e))

            except Exception as e:
                logging.error('Unexpected error occurred: {0}'.format(e))

    def request_message_processing(self, channel, method_frame, header_frame, body):
        photo_id, photo_bytes = self.message_packer.unpack_the_message_body(body)

        try:
            model_result = self.submit_for_processing(photo_bytes, photo_id)

            AppendResultsCommand().execute(model_result)

            message_with_event = self.message_packer.pack_the_result_message_body(photo_id)

            self.publish_message_to_exchange(
                rabbitmq_results_exchange_name,
                message_with_event,
            )
            logging.warning(f'Event {processing_result_event_name} for photo with id {photo_id} sended.')

        except Exception as e:
            logging.error('Unexpected error occurred: {0}'.format(e))
            retry_count = self.find_retry_count(header_frame)

            if retry_count >= rabbitmq_models_max_retry_number:
                channel.basic_ack(delivery_tag=method_frame.delivery_tag)
                logging.info('Cannot be processed.')
            else:
                channel.basic_reject(delivery_tag=method_frame.delivery_tag, requeue=False)
                logging.info('Message rejected.')
            return

        channel.basic_ack(delivery_tag=method_frame.delivery_tag)

    @staticmethod
    def find_retry_count(header_frame):
        retry_count = 0
        if header_frame.headers is not None and 'x-death' in header_frame.headers:
            retry_count = header_frame.headers['x-death'][0]['count']
        return retry_count

    def publish_message_to_exchange(self,
                                    exchange_name,
                                    message,
                                    exchange_type='fanout'):
        channel = self.connection.channel()
        channel.exchange_declare(exchange=exchange_name,
                                 exchange_type=exchange_type)

        try:
            channel.basic_publish(
                exchange=exchange_name,
                routing_key='',
                body=json.dumps(message).encode('utf-8'),
                properties=BasicProperties(
                    delivery_mode=2,
                )
            )
        except Exception:
            logging.warning('Aborting...')
            self.connection.close()

    def submit_for_processing(
        self, 
        photo_bytes, 
        photo_id,
        ):
        processing_result = self.model.process_data(photo_bytes)
        validated_model_result = ModelResultSchema(
                photo_id=photo_id,
                model_type=self.model_type,
                result=processing_result,
            ).dict()

        return validated_model_result
