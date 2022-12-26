import os

from pymongo import MongoClient


class Repository():
    def __init__(self, collection):
        mongoclient = MongoClient(os.environ["DB_CONNECTION_STRING"])
        database = mongoclient["production"]
        self.collection = database[collection]

    def insert(self, doc):
        return self.collection.insert_one(doc)

    def insert_many(self, docs):
        return self.collection.insert_many(docs)

    def read_all(self):
        return self.collection.find()

    def read_many(self, conditions, projection=None):
        return self.collection.find(conditions, projection)

    def read(self, conditions):
        return self.collection.find_one(conditions)

    # Update operations
    def update(self, conditions, new_value):
        return self.collection.update_one(conditions, new_value)

    # Delete operations
    def delete(self, condition):
        return self.collection.delete_one(condition)

    def delete_many(self, condition):
        return self.collection.delete_many(condition)
