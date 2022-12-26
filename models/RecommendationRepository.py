import logging
from models.Repository import Repository

logger = logging.getLogger('botlogs')


class RecommendationRepository(Repository):
    def __init__(self):
        super().__init__("recommendations")
