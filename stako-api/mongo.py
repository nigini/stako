from pymongo import MongoClient
from bson.objectid import ObjectId
from bson.json_util import loads, dumps
import uuid
from datetime import datetime
import logging
from stackoverflow import Question

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
		a_user = collection.find_one({'UUID': user_uuid}, {'_id': 0})
		if a_user:
			return loads(dumps(a_user))
		else:
			return {}


class UserSummary:
	def __init__(self, settings):
		self.client = MongoClient(settings.MONGODB_URL)
		self.db = self.client[settings.MONGODB_NAME]
		self.api = APIMongo(settings)

	def update_user(self, uuid):
		user = self.api.get_user(uuid)
		if user:
			last_updated = user['activity']['updated']
			activities = self.db[COLLECTION_ACTIVITIES]
			user_act = activities.find({'UUID': uuid}, {'_id': 0})
			question_ids = Question.get_question_keys(user_act).keys()
			questions_data = Question.get_questions(question_ids)
			for q in questions_data:
				# TODO
				pass

