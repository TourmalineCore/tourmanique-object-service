import logging
from config.model_config import model_type

from domain import Object
from domain import PhotoObject

from helpers.get_from_db_or_create import get_from_db_or_create
from pydantic import BaseModel

from domain.data_access_layer.session import session



class NewPhotoObjectCommand:
    def __init__(self):
        pass
    
    def create(self, object_entity: Object, photo_id: int):
        with session() as current_session:
            # object_instance = get_from_db_or_create(Object, name=object_entity.name)
            object_instance = current_session \
                    .query(Object) \
                    .filter_by(name=object_entity.name)\
                    .first()

            if object_instance:
                object_id = object_instance.id
            else:
                object_instance = Object(name=object_entity.name)
                current_session.add(object_instance)
                current_session.commit()
                object_id = object_instance.id


        # with session() as current_session:
            current_session.add(PhotoObject(photo_id=photo_id,
                                            object_id=object_id))
            current_session.commit()


class ObjectSchema(BaseModel):
    name: str

    class Config:
        orm_mode = True


insert_to_db_commands = {
    'objects-model': NewPhotoObjectCommand,
}

map_result_to_entity = {
    'objects-model': Object,
}

validate_result_with_schema = {
    'objects-model': ObjectSchema,
}

class AppendResultsCommand:
    @staticmethod
    def execute(result_message):
        for result in result_message['result']:
            valid_result = validate_result_with_schema[model_type](**result)
            result_entity = map_result_to_entity[model_type](**valid_result.dict())

            insert_to_db_command = insert_to_db_commands[model_type]
            insert_to_db_command().create(
                result_entity, 
                result_message['photo_id'],
                )
