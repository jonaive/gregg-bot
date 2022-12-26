import logging
from collections import defaultdict
from datetime import datetime

import pymongo

from models.Repository import Repository

logger = logging.getLogger('botlogs')


class EventRepository(Repository):
    def __init__(self):
        super().__init__("events")

    def get_events(self, type="BR", status="present", announced=True):
        if status != "requested":
            filter_by = self.create_date_filter(type, status)
        else:
            filter_by = {"$and": []}
            filter_by["$and"].append({"type": type})
        if announced is True:
            filter_by["$and"].append({"announce_id": {"$ne": None}})
        else:
            filter_by["$and"].append({"announce_id": {"$eq": None}})

        events = self.read_many(filter_by).sort([
            ("start_date", pymongo.ASCENDING),
            ("end_date", pymongo.DESCENDING)
        ])
        if status == "past":
            events = events.sort([('start_date', pymongo.DESCENDING),
                                  ('end_date', pymongo.ASCENDING)])
        return events

    def create_date_filter(self, event_type, status):
        filter_by = {"$and": []}
        timestamp = datetime.utcnow().timestamp()
        if event_type is not None:
            filter_by["$and"].append({"type": event_type})
        if status == "present":
            filter_by["$and"].append({"start_date": {"$lte": timestamp}})
            filter_by["$and"].append({"end_date": {"$gte": timestamp}})
        elif status == "past":
            filter_by["$and"].append({"start_date": {"$lt": timestamp}})
            filter_by["$and"].append({"end_date": {"$lt": timestamp}})
        if status == "future":
            filter_by["$and"].append({"start_date": {"$gt": timestamp}})
            filter_by["$and"].append({"end_date": {"$gt": timestamp}})
        return filter_by

    def get_all_readers(self):
        events = self.read_all()
        results = []
        user_dict = self.calculate_all_scores(events)
        for user_id in sorted(user_dict, key=user_dict.get, reverse=True):
            results.append((user_id, user_dict[user_id]))
        return results

    def calculate_score(self, user_id: int):
        score = {"BR": 0, "MR": 0}
        events = self.read_many(
            {"$or": [{"read_by": user_id},
                     {"requested_by": user_id}]
             })
        for event in events:
            if "reader_points" in event and \
                    (user_id in event["read_by"] or str(user_id) in event['read_by']):
                print(event['book']['title'], event['type'])
                score[event["type"]] += event['reader_points']
            if "leader_points" in event and \
                    (user_id in event["requested_by"] or str(user_id) in event["requested_by"]):
                print('x', event['book']['title'], event['type'])
                score[event["type"]] += event['leader_points']
            print(score)
        return score

    def calculate_all_scores(self, events):
        user_dict = defaultdict(int)
        for event in events:
            for user in event['read_by']:
                user = int(user)
                if "reader_points" in event:
                    user_dict[user] += event['reader_points']
            for user in event['requested_by']:
                user = int(user)
                if "leader_points" in event:
                    user_dict[user] += event['leader_points']
        return user_dict

    def get_user_participated_events(self, user_id: int, event_type):
        return list(self.read_many(
            {"read_by": user_id, "type": event_type}).sort([('start_date', pymongo.DESCENDING),
                                                            ('end_date', pymongo.ASCENDING)]))

    def get_user_interacted_events(self, user_id: int, event_type):
        timestamp = datetime.utcnow().timestamp()
        return list(self.read_many(
            {
                "$or":
                [{"request_reactors": user_id},
                 {"announce_reactors": user_id}
                 ],
                "type": event_type,
                "end_date": {"$gte": timestamp}
            }).sort([('start_date', pymongo.DESCENDING), ('end_date', pymongo.ASCENDING)]))
