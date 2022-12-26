import logging
from models.Repository import Repository

logger = logging.getLogger('botlogs')


class UserRepository(Repository):
    def __init__(self):
        super().__init__("users")

    def add_or_update(self, user):
        try:
            if super().read({"id": user["id"]}) is None:
                logger.info(f"Added user: {user}")
                super().insert(user)
            else:
                logger.info(f"Updated user: {user}")
                super().update({"id": user["id"]}, {"$set": user})
        except Exception as e:
            logger.error(f"Error adding/updating user - {user}: {e}")
        return
