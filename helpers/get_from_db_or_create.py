from domain.data_access_layer.session import session


def get_from_db_or_create(model, **kwargs):
    with session() as current_session:
        instance = current_session \
            .query(model) \
            .filter_by(**kwargs)\
            .first()

        if instance:
            return instance
        else:
            instance = model(**kwargs)
            current_session.add(instance)
            current_session.commit()
            return instance