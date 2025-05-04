from flask import Blueprint

from routes.queries.get_objects_query import GetObjectsQuery

objects_blueprint = Blueprint('results', __name__, url_prefix='/results')


@objects_blueprint.route('/<int:photo_id>', methods=['GET'])
def get_objects_by_photo_id(photo_id):
    objects_entities = GetObjectsQuery().by_photo_id(photo_id)
    objects_response = [object_entity.name for object_entity in objects_entities]

    return objects_response