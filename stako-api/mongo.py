from pymongo import MongoClient
from bson.objectid import ObjectId
from bson.json_util import loads, dumps
import uuid
from datetime import datetime
import logging
import copy
from stackoverflow import Question
from data import StakoUser

#from celery import Celery
#queue = Celery()
COLLECTION_AUTH = 'authorizations'
COLLECTION_USERS = 'users'
COLLECTION_ACTIVITIES = 'activities'


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
				empty_user = StakoUser.get_empty_user()
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


class UserSummary:
	def __init__(self, settings):
		client = MongoClient(settings.MONGODB_URL)
		db = client[settings.MONGODB_NAME]
		self.db_activities = db[COLLECTION_ACTIVITIES]
		self.api = APIMongo(settings)
		self.so_questions = Question(settings.STAKO_TEST)

	def update_user(self, uuid, reset=False, act_newer_then_gmt_timestamp=None):
		user = self.api.get_user(uuid)
		if user:
			user_act = self._get_user_activities(uuid, act_newer_then_gmt_timestamp)
			if reset:
				user['activity']['weekly_summary'] = StakoUser.get_empty_weekly_summary()
			else:
				user['activity']['updated'] = int(datetime.utcnow().timestamp())
			last_updated = user['activity']['weekly_summary']
			act_questions_ids = self.so_questions.get_visits_questions_keys(user_act)
			questions_data = self.so_questions.get_questions(act_questions_ids.keys())
			for question_id, activity in act_questions_ids.items():
				isotime = datetime.fromtimestamp(activity['timestamp']).isocalendar()
				year = str(isotime[0])
				week = str(isotime[1])
				empty_summary = StakoUser.get_empty_weekly_summary(year, week)
				if not last_updated.get(year, None):
					last_updated[year] = {}
				if not last_updated[year].get(week, None):
					last_updated[year][week] = copy.deepcopy(empty_summary[year][week])
					last_updated[year][week]['top_tags'].pop('top_tag', None)
				for tag in questions_data[question_id]['tags']:
					if tag not in last_updated[year][week]['top_tags'].keys():
						last_updated[year][week]['top_tags'][tag] = \
							copy.deepcopy(empty_summary[year][week]['top_tags']['top_tag'])
					last_updated[year][week]['top_tags'][tag]['pages_visited'] += 1
				last_updated[year][week]['pages_visited'] += 1
			return self.api.save_user(user)
		return False

	def _get_user_activities(self, uuid, act_newer_then_gmt_timestamp):
		search_obj = {'uuid': uuid}
		if act_newer_then_gmt_timestamp:
			search_obj['timestamp'] = {'$gt': int(act_newer_then_gmt_timestamp)}
		return self.db_activities.find(search_obj, {'_id': 0})
