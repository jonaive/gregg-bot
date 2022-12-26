import logging

from models.Repository import Repository

logger = logging.getLogger('botlogs')


class SprintRepository(Repository):
    def __init__(self):
        super().__init__("sprints")

    def save(self, sprint):
        try:
            sprint_doc = {
                "channel_id": sprint.id,
                "start_timestamp": sprint.start_timestamp,
                "duration": sprint.duration,
                "participants": list(sprint.end_counts.keys()),
                "start_counts": {str(key): value for key, value in sprint.start_counts.items()},
                "end_counts": {str(key): value for key, value in sprint.end_counts.items()}
            }
            self.insert(sprint_doc)
            logger.info(f"Inserted sprint {sprint_doc['channel_id']} into database")
        except Exception as e:
            logger.error(f"{e}\nError inserting sprint to db")
        return

    def calculate_stats(self, user_id: int):
        sprints = self.read_many({"participants": user_id})
        res = {"count": 0, "duration": 0, "page_count": 0}
        for sprint in sprints:
            res['count'] += 1
            res['duration'] += sprint['duration']
            res['page_count'] += sprint['end_counts'][str(
                user_id)] - sprint['start_counts'][str(user_id)]
        return res
