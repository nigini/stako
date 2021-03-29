from pymongo import MongoClient
from bson.objectid import ObjectId
from bson.json_util import loads, dumps
from datetime import datetime
import logging
import copy
import secrets
from stako.api.data.stackoverflow import Question
import stako.api.data.data as stako_data
from stako.api.data.data import StakoUser, Experiment, StakoActivity

COLLECTION_AUTH = 'authorizations'
COLLECTION_USERS = 'users'
COLLECTION_ACTIVITIES = 'activities'
COLLECTION_NOTIFICATIONS = 'notifications'


class ExperimentMongo:
	def __init__(self, settings):
		self.client = MongoClient(settings.MONGODB_URL)
		self.db = self.client[settings.MONGODB_NAME]
		self.experiment = self.db[COLLECTION_AUTH]
		self.data = Experiment(settings)

	def add_participant(self, email):
		stako_users = self.db[COLLECTION_USERS]
		if self.get_participant(email) == {}:
			a_user = self.data.get_empty_user()
			a_user['email'] = email
			result = self.experiment.insert_one(a_user)
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
					self.experiment.delete_one({"_id": result.inserted_id})
		return None

	def _update_participant(self, participant):
		result = self.experiment.update_one({'email': participant['email']}, {'$set': participant}, upsert=False)
		if result.modified_count == 1:
			return True
		else:
			return False

	def regen_participant_passkey(self, email):
		participant = self.get_participant(email)
		if participant == {}:
			return None
		else:
			pass_key = secrets.token_hex(20)
			participant['pass_hash'] = stako_data.string_hash(pass_key)
			updated = self._update_participant(participant)
			if updated:
				return pass_key
			else:
				return None


	# Makes sure the role is part of this participant's roles
	def add_participant_role(self, email, role):
		p = self.get_participant(email)
		result = False
		if p:
			if role in self.data.ROLES:
				if role not in p['roles']:
					p['roles'].append(role)
					result = self._update_participant(p)
				else:
					result = True
		return result

	# Makes sure the role is NOT part of this participant's roles
	def remove_participant_role(self, email, role):
		p = self.get_participant(email)
		result = False
		if p:
			if role in p['roles']:
				p['roles'].remove(role)
				result = self._update_participant(p)
			else:
				result = True
		return result

	# Ensures participant is part of experiment <exp_name> and in group <exp_group>
	# <exp_name> and <exp_group> HAVE TO be in data.Experiment
	def add_participant_experiment(self, email, exp_name, exp_group):
		p = self.get_participant(email)
		result = False
		if p:
			if 'experiments' not in p.keys():
				p['experiments'] = {}
			if exp_name in self.data.EXPERIMENTS.keys():
				if exp_group in self.data.EXPERIMENTS[exp_name]:
					p['experiments'][exp_name] = exp_group
					result = self._update_participant(p)
		return result

	# Ensures participant is NOT part of experiment <exp_name>
	# <exp_name> HAS TO be in data.Experiment
	def remove_participant_experiment(self, email, exp_name):
		p = self.get_participant(email)
		result = False
		if p:
			if 'experiments' not in p.keys():
				p['experiments'] = {}
			if exp_name in p['experiments'].keys():
				p['experiments'].pop(exp_name, None)
				result = self._update_participant(p)
			else:
				result = True
		return result

	def get_participant(self, by_value, by_key='email'):
		collection = self.db[COLLECTION_AUTH]
		if isinstance(by_value, str):
			by_value = by_value.lower()
		a_user = collection.find_one({by_key: by_value}, {'_id': 0})
		if a_user:
			return loads(dumps(a_user))
		else:
			return {}

	def get_all(self):
		collection = self.db[COLLECTION_AUTH]
		return collection.find({}, {'_id': 0})


class APIMongo:

	def __init__(self, settings):
		self.client = MongoClient(settings.MONGODB_URL)
		self.db = self.client[settings.MONGODB_NAME]

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

	def get_activities(self, user_uuid, a_type=StakoActivity.ACTIVITY_TYPE_SO_VISIT):
		collection = self.db[COLLECTION_ACTIVITIES]
		result = collection.find({'uuid': user_uuid, 'type': a_type}, {'_id': 0, 'url': 1, 'timestamp': 1})
		to_return = []
		if result:
			for act in result:
				to_return.append(act)
		return to_return

	def get_notifications(self, user_uuid):
		collection = self.db[COLLECTION_NOTIFICATIONS]
		notifications = collection.find({'uuid': user_uuid, 'delivered': None}, {'_id': 0})
		to_return = []
		if notifications:
			pass
		return to_return



class UserSummary:
	def __init__(self, settings):
		client = MongoClient(settings.MONGODB_URL)
		db = client[settings.MONGODB_NAME]
		self.db_activities = db[COLLECTION_ACTIVITIES]
		self.api = APIMongo(settings)
		self.so_questions = Question()

	def update_user(self, uuid, reset=False, act_newer_then_gmt_timestamp=None):
		user = self.api.get_user(uuid)
		if user:
			user_act = self._get_user_activities(uuid, act_newer_then_gmt_timestamp)
			if reset:
				user['activity']['weekly_summary'] = StakoUser.get_empty_weekly_summary()
			else:
				user['activity']['updated'] = stako_data.get_utc_timestamp()
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
