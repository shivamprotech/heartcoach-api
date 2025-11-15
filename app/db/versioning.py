# app/db/versioning.py
from sqlalchemy_continuum import make_versioned, versioning_manager
from app.core.context import current_user_id

make_versioned(user_cls='app.models.User')


def get_current_user():
    # Return the UUID stored in the contextvar
    return current_user_id.get()


versioning_manager.transaction_cls.current_user = property(
    lambda self: get_current_user()
)
