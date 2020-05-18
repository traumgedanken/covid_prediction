import os

import pymongo
import dotenv

dotenv.load_dotenv()


def get_db_instance():
    mongo_url = os.getenv('MONGO_URL')
    client = pymongo.MongoClient(mongo_url)
    return client.get_database('covid')
