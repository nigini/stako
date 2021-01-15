from pymongo import MongoClient
from bson.objectid import ObjectId
from bson.json_util import loads, dumps
import uuid
from datetime import datetime
import logging

#from celery import Celery
#queue = Celery()
COLLECTION_AUTH = 'authorizations'
COLLECTION_USERS = 'users'
COLLECTION_ACTIVITIES = 'activities'


class DataStructure:

	@staticmethod
	def get_empty_user():
		return {
			"nickname": "",
			"uuid": str(uuid.uuid4()),
			"motto": "",
			"start_date": int(datetime.timestamp(datetime.utcnow())),
			"activity": {
				"weekly_summary": [
					{
						"year": 2021,
						"week": 0,
						"top_tags": [
							{
								"tag_name": "",
								"pages_visits": 0
							}
						],
						"pages_visits": 0
					}
				],
				"updated": int(datetime.timestamp(datetime.utcnow()))
			}
		}


class ExperimentMongo:
	ROLES = ['participant', 'researcher']

	def __init__(self, settings):
		self.client = MongoClient(settings.MONGODB_URL)
		self.db = self.client[settings.MONGODB_NAME]

	def add_user(self, email):
		experiment = self.db[COLLECTION_AUTH]
		stako_users = self.db[COLLECTION_USERS]
		if self.get_user(email) == {}:
			a_user = self._get_empty_user()
			a_user['email'] = email
			result = experiment.insert_one(a_user)
			saved = type(result.inserted_id) is ObjectId
			logging.info('[Mongo:SaveExperimentUser] Saved? {}'.format(saved))
			if saved:
				empty_user = DataStructure.get_empty_user()
				empty_user['uuid'] = a_user['uuid']
				result2 = stako_users.insert_one(empty_user)
				saved2 = type(result2.inserted_id) is ObjectId
				if saved2:
					return a_user['uuid']
				else:
					experiment.delete_one({"_id": result.inserted_id})
		return None

	def add_role(self, email, role):
		pass

	def remove_role(self, email, role):
		pass

	def get_user(self, email):
		collection = self.db[COLLECTION_AUTH]
		a_user = collection.find_one({'email': email}, {'_id': 0})
		if a_user:
			return loads(dumps(a_user))
		else:
			return {}

	@staticmethod
	def _get_empty_user():
		return {
			'uuid': str(uuid.uuid4()),
			'email': '',
			'roles': []
		}


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