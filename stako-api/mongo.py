from pymongo import MongoClient
from bson.objectid import ObjectId
from bson.json_util import loads, dumps
import logging

#from celery import Celery
#queue = Celery()
COLLECTION_USERS = 'users'
COLLECTION_ACTIVITIES = 'activities'

class APIMongo:

	def __init__(self, settings):
		self.client = MongoClient(settings.MONGODB_URL)
		self.db = self.client[settings.MONGODB_NAME]
		#queue = Celery('mongo', broker=settings.BROKER_URL)

	def save_user(self, user):
		collection = self.db[COLLECTION_USERS]
		result = collection.update_one({'uuid': user['uuid']}, {'$set': user}, upsert=True)
		logging.info('[Mongo:SaveUser] Result: {}'.format(result.raw_result))

		if result.upserted_id or result.modified_count == 1:
			return True
		else:
			return False

	def get_user(self, user_value, user_key='uuid'):
		collection = self.db[COLLECTION_USERS]
		a_user = collection.find_one({user_key: user_value}, {'_id': 0})
		if a_user:
			return loads(dumps(a_user))
		else:
			return {}

	def save_activity(self, activity):
		collection = self.db[COLLECTION_ACTIVITIES]
		result = collection.insert_one(activity)
		saved = type(result.inserted_id) is ObjectId
		logging.info('[Mongo:SaveActivity] Saved? {}'.format(saved))
		return saved

	def get_activities(self, user_uuid):
		collection = self.db[COLLECTION_ACTIVITIES]
		a_user = collection.find_one({'uuid': user_uuid}, {'_id': 0})
		if a_user:
			return loads(dumps(a_user))
		else:
			return {}


#	@queue.task
	def save_questions(self, questions_list):
		#TODO test format
		collection = self.db['questions']
		#TODO check updates before creating new entries (QUESTIONID and LASTUPDATE?)
		collection.insert_many(questions_list)

	def get_questions(self, tag_list, size):
		collection = self.db['questions']
		# TODO Index collection by tags
		result = collection.aggregate([
			{'$match': {'tags': {'$all': tag_list}}},
			{'$sample': {'size': size}}])
		return list(result)

	def get_teams(self, tag_list):
		collection = self.db['teams']
		tag_list.sort()
		# TODO Index collection by tags
		result = collection.find({
			'tags': {
				'$size': len(tag_list),
				'$all': tag_list
			}}, {'_id': 0})
		return loads(dumps(result))

	def save_team(self, team):
		collection = self.db['teams']
		a_team = self._get_team(team['id'])
		if a_team is not None:
			a_team['last_updated'] = team['last_updated']
		else:
			a_team = team
		collection.save(a_team)

	def get_team(self, team_id):
		collection = self.db['teams']
		a_team = collection.find_one({'id': team_id}, {'_id': 0})
		return loads(dumps(a_team))

#	@queue.task
	def save_message(self, message, channel='team_test'):
		pass