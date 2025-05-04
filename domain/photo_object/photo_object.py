from domain.data_access_layer.db import db


class PhotoObject(db.Model):
    __tablename__ = 'photo_object'

    photo_id = db.Column(db.BigInteger, nullable=False, primary_key=True)
    object_id = db.Column(db.BigInteger, db.ForeignKey('objects.id'), primary_key=True)

    object = db.relationship("Object", back_populates='photo_object')

    def __repr__(self):
        return f'<PhotoObject photo_id:{self.photo_id!r} object_id:{self.object_id!r}>'