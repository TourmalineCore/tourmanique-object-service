from domain.data_access_layer.session import session
from domain import PhotoObject, Object


class GetObjectsQuery:
    def __init__(self):
        pass

    def by_photo_id(self, photo_id):
        with session() as current_session:
            return current_session \
                .query(Object) \
                .join(PhotoObject) \
                .filter(PhotoObject.photo_id == photo_id) \
                .all()

    def by_name(self, object_name):
        with session() as current_session:
            return current_session \
                .query(Object) \
                .filter(Object.name == object_name) \
                .one_or_none()