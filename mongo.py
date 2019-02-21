import settings
from pymongo import MongoClient
from celery import Celery

client = MongoClient(settings.MONGODB_URL)
db = client[settings.MONGODB_NAME]

queue = Celery('tasks', broker=settings.BROKER_URL)


@queue.task
def mongo_save_questions(questions_list):
	#TODO test format
	collection = db['questions']
	#TODO check updates before creating new entries (QUESTIONID and LASTUPDATE?)
	collection.insert_many(questions_list)


def mongo_get_questions(tag_list, size):
	collection = db['questions']
	#TODO Index collection by tags
	result = collection.aggregate([
		{ '$match': { 'tags': { '$all': tag_list } } }, 
		{ '$sample': { 'size': size } } ])
	return list(result)
