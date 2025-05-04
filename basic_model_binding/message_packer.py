import json

from helpers.s3_helper import S3Helper
from config.model_config import processing_result_event_name


class MessagePacker:
    def __init__(self, model_type):
        self.model_type = model_type

    @staticmethod
    def unpack_the_message_body(message_body):
        message_str = message_body.decode('utf-8')
        message = json.loads(message_str)

        photo_id = message["photo_id"]
        photo_bytes = S3Helper() \
            .s3_download_file(file_path_in_bucket=f'/{message["path_to_photo_in_s3"]}')

        return photo_id, photo_bytes

    def pack_the_result_message_body(self, photo_id: int):
        message_body = {
                'photo_id': photo_id,
                'event': processing_result_event_name,
            }

        return message_body
