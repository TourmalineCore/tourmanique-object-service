from domain.data_access_layer.db import db


class Object(db.Model):
    __tablename__ = 'objects'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    name = db.Column(db.String(2048), nullable=False)

    photo_object = db.relationship("PhotoObject", back_populates='object')

    def __repr__(self):
        return f'<Object {self.id!r} name:{self.name!r}>'