import unittest
import time
from pymongo import MongoClient
import json
from datetime import datetime
import stako.settings as settings
import stako.api.data.mongo as mongo
from stako.api.data.mongo import ExperimentMongo
import stako.api.data.data as stako_data
from stako.api.data.data import StakoActivity

from stako.api.api import app, AuthGoogle, AuthStako
ACTIVITY_TYPE_SO_VISIT = StakoActivity.ACTIVITY_TYPE_SO_VISIT
ACTIVITY_TYPE_SO_CLICK = StakoActivity.ACTIVITY_TYPE_SO_CLICK

URL = 'http://127.0.0.1:5000/v1/'
URL_AUTHG = URL + 'auth/google?email={}&google_id={}&token={}'
URL_AUTHS = URL + 'auth/stako?email={}&pass_key={}'
URL_ACTIVITY = URL + 'user/{}/activity/'
URL_ACTIVITY_TIME = '?date_start={}&date_end={}'
URL_ACTIVITY_TIME_S = '?date_start={}'
URL_ACTIVITY_TIME_E = '?date_end={}'
URL_EXPERIMENT = URL + 'user/{}/experiment/'
URL_NOTIFICATION = URL + 'user/{}/notification/'


class TestAPI(unittest.TestCase):
	def setUp(self):
		settings.STAKO_TEST = True
		settings.MONGODB_NAME = settings.MONGODB_NAME_TEST
		settings.STAKO_EXPERIMENTS = {
			"test": ['group_a', 'group_b', 'control'],
			"test2": ['group2_a', 'group2_b', 'control']
		}
		# CLEAN DB
		client = MongoClient(settings.MONGODB_URL)
		db = client[settings.MONGODB_NAME_TEST]
		users = db[mongo.COLLECTION_USERS]
		users.drop()
		activities = db[mongo.COLLECTION_ACTIVITIES]
		activities.drop()
		experiment = db[mongo.COLLECTION_AUTH]
		experiment.drop()
		self.experiment_mongo = ExperimentMongo(settings)
		# ADD TEST USER
		self.tester_g_uuid = self.experiment_mongo.add_participant(AuthGoogle.TESTER_EMAIL)
		self.assertIsNotNone(self.tester_g_uuid)
		self.tester_s_uuid = self.experiment_mongo.add_participant(AuthStako.TESTER_EMAIL)
		self.assertIsNotNone(self.tester_s_uuid)
		self.some_other_user_uuid = self.experiment_mongo.add_participant('not_authorized@stako.org')
		self.assertIsNotNone(self.some_other_user_uuid)
		self.real_user_email = 'tester@stako.org'
		self.real_user_uuid = self.experiment_mongo.add_participant(self.real_user_email)
		self.assertIsNotNone(self.real_user_uuid)
		self.real_user_passkey = self.experiment_mongo.regen_participant_passkey(self.real_user_email)


class TestAuthStakoAPI(TestAPI):
	def test_auth(self):
		app.config['JWT_ACCESS_TOKEN_EXPIRES'] = settings.STAKO_JWT_TOKEN_EXPIRES
		with app.test_client() as client:
			response = client.get(URL + 'auth/stako')
			self.assertEqual(400, response.status_code)
			response = client.get(URL_AUTHS.format('', ''))
			self.assertEqual(401, response.status_code)
			response = client.get(URL_AUTHS.format(AuthStako.TESTER_EMAIL, ''))
			self.assertEqual(200, response.status_code)
			response = client.get(URL_AUTHS.format(AuthGoogle.TESTER_EMAIL, ''))
			self.assertEqual(401, response.status_code)

			# THE REAL DEAL
			now = stako_data.get_utc_timestamp()
			delta = settings.STAKO_JWT_TOKEN_EXPIRES

			response = client.get(URL_AUTHS.format(self.real_user_email, 'NOT_THE_PASS_KEY'))
			self.assertEqual(401, response.status_code)
			response = client.get(URL_AUTHS.format(self.real_user_email, self.real_user_passkey))
			self.assertEqual(200, response.status_code)

			auth_token = response.get_json()
			self.assertEqual(self.real_user_uuid, auth_token['uuid'])
			self.assertRegex(auth_token['access_token'], '[a-zA-Z0-9-_]+?.[a-zA-Z0-9-_]+?.([a-zA-Z0-9-_]+)[/a-zA-Z0-9-_]+?$')
			self.assertTrue(isinstance(auth_token['expiration'], int))
			# This can fail by a second if the server call is at the moment where the second changes (1/1000 chance)?
			self.assertTrue(auth_token['expiration'] > 0)
			print("start: {}, delta: {}, sum: {}".format(now, delta, now+delta))
			print(auth_token)
			self.assertTrue(auth_token['expiration'] == now+delta or auth_token['expiration'] == now+delta-1)



class TestAuthAPI(TestAPI):
	def test_auth(self):
		app.config['JWT_ACCESS_TOKEN_EXPIRES'] = settings.STAKO_JWT_TOKEN_EXPIRES
		with app.test_client() as client:
			# NO EMAIL, NO GOOGLE_ID, NOR TOKEN
			response = client.get(URL + 'auth/google')
			self.assertEqual(400, response.status_code)
			# INVALID EMAIL, GOOGLE_ID, AND TOKEN
			response = client.get(URL_AUTHG.format('', '', ''))
			self.assertEqual(401, response.status_code)

			now = stako_data.get_utc_timestamp()
			delta = settings.STAKO_JWT_TOKEN_EXPIRES
			response = client.get(URL_AUTHG.format(AuthGoogle.TESTER_EMAIL, '', ''))
			self.assertEqual(200, response.status_code)
			auth_token = response.get_json()
			self.assertEqual(self.tester_g_uuid, auth_token['uuid'])
			self.assertRegex(auth_token['access_token'], '[a-zA-Z0-9-_]+?.[a-zA-Z0-9-_]+?.([a-zA-Z0-9-_]+)[/a-zA-Z0-9-_]+?$')
			self.assertTrue(isinstance(auth_token['expiration'], int))
			# This can fail by a second if the server call is at the moment where the second changes (1/1000 chance)?
			self.assertTrue(auth_token['expiration'] > 0)
			self.assertTrue(auth_token['expiration'] == now+delta or auth_token['expiration'] == now+delta-1)
			# TEST case non-sensitive email
			response = client.get(URL_AUTHG.format(AuthGoogle.TESTER_EMAIL.upper(), '', ''))
			self.assertEqual(200, response.status_code)
			auth_token = response.get_json()
			self.assertEqual(self.tester_g_uuid, auth_token['uuid'])
			self.assertRegex(auth_token['access_token'], '[a-zA-Z0-9-_]+?.[a-zA-Z0-9-_]+?.([a-zA-Z0-9-_]+)[/a-zA-Z0-9-_]+?$')
			self.assertTrue(isinstance(auth_token['expiration'], int))


			# TODO: CREATE VALID EMAIL, GOOGLE_ID, AND TOKEN
			# TEST GET_USER
			response = client.get(URL + 'user/{}/'.format(self.tester_g_uuid))
			self.assertEqual(401, response.status_code)
			header = {'Authorization': 'Bearer {}'.format(auth_token['access_token'])}
			response = client.get(URL + 'user/{}/'.format(self.tester_g_uuid), headers=header)
			self.assertEqual(200, response.status_code)
			self.assertEqual(self.tester_g_uuid, response.get_json()['uuid'])

			# CATCH IMPERSONATION
			response = client.get(URL + 'user/{}/'.format(self.some_other_user_uuid), headers=header)
			self.assertEqual(403, response.status_code)

	def test_auth_expiration(self):
		app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 1
		with app.test_client() as client:
			print('TOKEN EXPIRATION TIME: {}'.format(app.config['JWT_ACCESS_TOKEN_EXPIRES']))
			response = client.get(URL_AUTHG.format(AuthGoogle.TESTER_EMAIL, '', ''))
			self.assertEqual(200, response.status_code)
			auth_token = response.get_json()
			self.assertEqual(self.tester_g_uuid, response.get_json()['uuid'])
			header = {'Authorization': 'Bearer {}'.format(auth_token['access_token'])}
			response = client.get(URL + 'user/{}/'.format(self.tester_g_uuid), headers=header)
			self.assertEqual(200, response.status_code)
			self.assertEqual(self.tester_g_uuid, response.get_json()['uuid'])
			time.sleep(2)
			#TOKEN EXPIRED
			response = client.get(URL + 'user/{}/'.format(self.tester_g_uuid), headers=header)
			self.assertEqual(401, response.status_code)


class TestUserAPI(TestAPI):
	def test_users_base(self):
		with app.test_client() as client:
			response = client.get(URL_AUTHG.format(AuthGoogle.TESTER_EMAIL, '', ''))
			self.assertEqual(200, response.status_code)
			auth_token = response.get_json()
			self.header = {'Authorization': 'Bearer {}'.format(auth_token['access_token'])}

			response = client.get(URL + 'user/{}/'.format(self.tester_g_uuid), headers=self.header)
			self.assertEqual(200, response.status_code)
			self.assertEqual(self.tester_g_uuid, response.get_json()['uuid'])

			user = response.get_json()
			self.assertEqual(self.tester_g_uuid, user['uuid'])
			self.assertTrue('nickname' in user)
			self.assertFalse('email' in user)
			self.assertTrue('motto' in user)
			self.assertTrue('activity' in user)
			self.assertTrue('start_date' in user)

	def test_users_update(self):
		with app.test_client() as client:
			response = client.get(URL_AUTHG.format(AuthGoogle.TESTER_EMAIL, '', ''))
			self.assertEqual(200, response.status_code)
			auth_token = response.get_json()
			header = {'Authorization': 'Bearer {}'.format(auth_token['access_token'])}
			response = client.get(URL + 'user/{}/'.format(self.tester_g_uuid), headers=header)
			self.assertEqual(200, response.status_code)

			# CHANGING USER DATA
			user = response.get_json()
			user['nickname'] = 'Tester'
			user['motto'] = 'I will test it all!'
			user['uuid'] = 'SHOULD_NOT_BE_CHANGED'
			user['email'] = 'cannotadd@stako.org'
			# Does not make a difference
			user.pop('activity', None)

			response = client.put(URL + 'user/{}/'.format(self.tester_g_uuid), data=json.dumps(user),
								  headers=header, content_type='application/json')
			self.assertEqual(200, response.status_code)
			# DID IT REALLY CHANGE?
			response = client.get(URL + 'user/{}/'.format(self.tester_g_uuid), headers=header)
			self.assertEqual(200, response.status_code)
			user2 = response.get_json()
			self.assertEqual(self.tester_g_uuid, user2['uuid'])
			self.assertEqual(user['nickname'], user2['nickname'])
			self.assertEqual(user['motto'], user2['motto'])
			self.assertEqual(user['start_date'], user2['start_date'])
			self.assertTrue('activity' in user2)
			self.assertFalse('email' in user2)


class TestActivityAPI(TestAPI):
	def setUp(self):
		super(TestActivityAPI, self).setUp()
		with app.test_client() as self.api:
			response = self.api.get(URL_AUTHG.format(AuthGoogle.TESTER_EMAIL, '', ''))
			self.assertEqual(200, response.status_code)
			auth_token = response.get_json()
			self.header = {'Authorization': 'Bearer {}'.format(auth_token['access_token'])}
			response = self.api.get(URL + 'user/{}/'.format(self.tester_g_uuid), headers=self.header)
			self.assertEqual(200, response.status_code)

	def test_get_activity(self):
		response = self.api.get(URL_ACTIVITY.format(self.tester_g_uuid), headers=self.header)
		self.assertEqual(200, response.status_code)
		data = response.get_json()
		self.assertTrue('activities' in data.keys())
		self.assertEqual(0, len(data['activities']))

		checkpoint1 = stako_data.get_utc_timestamp()
		an_activity = {
			'url': 'https://stackoverflow.com/questions/20001229/',
			'type': ACTIVITY_TYPE_SO_VISIT
		}
		response = self.api.post(URL_ACTIVITY.format(self.tester_g_uuid), data=json.dumps(an_activity),
								headers=self.header, content_type='application/json')
		self.assertEqual(200, response.status_code)

		response = self.api.get(URL_ACTIVITY.format(self.tester_g_uuid), headers=self.header)
		self.assertEqual(200, response.status_code)
		data = response.get_json()
		self.assertTrue('activities' in data.keys())
		self.assertEqual(1, len(data['activities']))
		self.assertEqual(an_activity['url'], data['activities'][0]['url'])

		time.sleep(2)
		checkpoint2 = stako_data.get_utc_timestamp()
		another_activity = {
			'url': 'https://stackoverflow.com/questions/44666648/',
			'type': ACTIVITY_TYPE_SO_VISIT
		}
		response = self.api.post(URL_ACTIVITY.format(self.tester_g_uuid), data=json.dumps(another_activity),
								headers=self.header, content_type='application/json')
		self.assertEqual(200, response.status_code)

		response = self.api.get(URL_ACTIVITY.format(self.tester_g_uuid), headers=self.header)
		self.assertEqual(200, response.status_code)
		data = response.get_json()
		self.assertTrue('activities' in data.keys())
		self.assertEqual(2, len(data['activities']))
		self.assertEqual(an_activity['url'], data['activities'][0]['url'])
		self.assertEqual(another_activity['url'], data['activities'][1]['url'])

		# TIME CONSTRAINT
		time.sleep(2)
		checkpoint3 = stako_data.get_utc_timestamp()
		url = URL_ACTIVITY.format(self.tester_g_uuid) + URL_ACTIVITY_TIME.format(checkpoint2, checkpoint3)
		response = self.api.get(url, headers=self.header)
		self.assertEqual(200, response.status_code)
		data = response.get_json()
		self.assertTrue('activities' in data.keys())
		self.assertEqual(1, len(data['activities']))
		self.assertEqual(another_activity['url'], data['activities'][0]['url'])

		url = URL_ACTIVITY.format(self.tester_g_uuid) + URL_ACTIVITY_TIME_E.format(checkpoint2-1)
		response = self.api.get(url, headers=self.header)
		self.assertEqual(200, response.status_code)
		data = response.get_json()

		self.assertTrue('activities' in data.keys())
		self.assertEqual(1, len(data['activities']))
		self.assertEqual(an_activity['url'], data['activities'][0]['url'])

		url = URL_ACTIVITY.format(self.tester_g_uuid) + URL_ACTIVITY_TIME_S.format(checkpoint2)
		response = self.api.get(url, headers=self.header)
		self.assertEqual(200, response.status_code)
		data = response.get_json()
		self.assertTrue('activities' in data.keys())
		self.assertEqual(1, len(data['activities']))
		self.assertEqual(another_activity['url'], data['activities'][0]['url'])


	def test_put_activity(self):
		with app.test_client() as client:
			response = client.get(URL_AUTHG.format(AuthGoogle.TESTER_EMAIL, '', ''))
			self.assertEqual(200, response.status_code)
			auth_token = response.get_json()
			header = {'Authorization': 'Bearer {}'.format(auth_token['access_token'])}
			response = client.get(URL + 'user/{}/'.format(self.tester_g_uuid), headers=header)
			self.assertEqual(200, response.status_code)

			# TODO: Test for all supported activity types!
			an_activity = {
				'url': 'https://stackoverflow.com/questions/20001229/',
				'type': ACTIVITY_TYPE_SO_VISIT
			}

			response = client.post(URL_ACTIVITY.format(self.tester_g_uuid), data=json.dumps(an_activity),
								   headers=header, content_type='application/json')
			self.assertEqual(200, response.status_code)
			saved_activity = response.get_json()
			self.assertEqual(self.tester_g_uuid, saved_activity['uuid'])
			self.assertEqual(an_activity['url'], saved_activity['url'])
			self.assertEqual(ACTIVITY_TYPE_SO_VISIT, saved_activity['type'])

			# NO URL or TYPE
			a_bad_activity = {}
			response = client.post(URL_ACTIVITY.format(self.tester_g_uuid), data=json.dumps(a_bad_activity),
								   headers=header, content_type='application/json')
			self.assertEqual(400, response.status_code)
			# BAD URL
			a_bad_activity = {'url': 'stackoverflow.com'}
			response = client.post(URL_ACTIVITY.format(self.tester_g_uuid), data=json.dumps(a_bad_activity),
								   headers=header, content_type='application/json')
			self.assertEqual(400, response.status_code)
			# MISSING ACTIVITY "TYPE"
			a_bad_activity = an_activity.copy()
			a_bad_activity.pop('type', None)
			response = client.post(URL_ACTIVITY.format(self.tester_g_uuid), data=json.dumps(a_bad_activity),
								   headers=header, content_type='application/json')
			self.assertEqual(400, response.status_code)
			# NON-EXISTING ACTIVITY TYPE
			a_bad_activity['type'] = 'NOT_VALID'
			response = client.post(URL_ACTIVITY.format(self.tester_g_uuid), data=json.dumps(a_bad_activity),
								   headers=header, content_type='application/json')
			self.assertEqual(400, response.status_code)

			# TESTING CLICK TYPE
			# MISSING DATA FOR VALID TYPE
			another_activity = an_activity.copy()
			another_activity['type'] = ACTIVITY_TYPE_SO_CLICK
			response = client.post(URL_ACTIVITY.format(self.tester_g_uuid), data=json.dumps(another_activity),
								   headers=header, content_type='application/json')
			self.assertEqual(400, response.status_code)

			# FIXING FOR click TYPE
			another_activity['element'] = 'USER:1234'
			response = client.post(URL_ACTIVITY.format(self.tester_g_uuid), data=json.dumps(another_activity),
								   headers=header, content_type='application/json')
			self.assertEqual(200, response.status_code)

			# NO USER
			response = client.post(URL_ACTIVITY.format('SOME_BROKEN_UUID'), data=json.dumps(an_activity),
									headers=header, content_type='application/json')
			self.assertEqual(403, response.status_code)

			# TODO Only admin can act on other's account
			# self.assertEqual(403, response.status_code)

			# TESTING CLICK TYPE COMMING FROM POPUP
			# MISSING DATA FOR VALID TYPE
			another_activity = an_activity.copy()
			another_activity['url'] = 'https://www.stako.org/extensions/chrome'
			another_activity['type'] = ACTIVITY_TYPE_SO_CLICK
			another_activity['element'] = 'TAG:1234'
			response = client.post(URL_ACTIVITY.format(self.tester_g_uuid), data=json.dumps(another_activity),
								   headers=header, content_type='application/json')
			self.assertEqual(200, response.status_code)


class TestExperimentAPI(TestAPI):

	def setUp(self):
		super(TestExperimentAPI, self).setUp()
		added = self.experiment_mongo.add_participant_experiment(AuthGoogle.TESTER_EMAIL, 'test', 'control')
		self.assertTrue(added)
		added = self.experiment_mongo.add_participant_experiment(AuthGoogle.TESTER_EMAIL, 'test2', 'group2_a')
		self.assertTrue(added)
		self.exp_name_test_hash = stako_data.string_hash('test')
		self.exp_group_test_hash = stako_data.string_hash('control')
		self.exp_name_test2_hash = stako_data.string_hash('test2')
		self.exp_group_test2_hash = stako_data.string_hash('group2_a')

	def test_experiments(self):
		with app.test_client() as client:
			response = client.get(URL_AUTHG.format(AuthGoogle.TESTER_EMAIL, '', ''))
			self.assertEqual(200, response.status_code)
			auth_token = response.get_json()
			header = {'Authorization': 'Bearer {}'.format(auth_token['access_token'])}
			response = client.get(URL + 'user/{}/'.format(self.tester_g_uuid), headers=header)
			self.assertEqual(200, response.status_code)
			# GET NON-EXISTENT PARTICIPANT
			response = client.get(URL_EXPERIMENT.format('NOT_VALID_USERID'), headers=header,
								  content_type='application/json')
			self.assertEqual(403, response.status_code)
			# VALID USER
			response = client.get(URL_EXPERIMENT.format(self.tester_g_uuid), headers=header,
								  content_type='application/json')
			self.assertEqual(200, response.status_code)
			u_experiments = response.get_json()
			self.assertEqual(self.tester_g_uuid, u_experiments['uuid'])
			self.assertEqual(2, len(u_experiments['experiments']))
			self.assertTrue(self.exp_name_test_hash in u_experiments['experiments'].keys())
			self.assertTrue(self.exp_name_test2_hash in u_experiments['experiments'].keys())
			self.assertEqual(self.exp_group_test_hash, u_experiments['experiments'][self.exp_name_test_hash])
			self.assertEqual(self.exp_group_test2_hash, u_experiments['experiments'][self.exp_name_test2_hash])


class TestNotificationAPI(TestAPI):

	def setUp(self):
		super(TestNotificationAPI, self).setUp()

	def test_experiments(self):
		with app.test_client() as client:
			response = client.get(URL_AUTHG.format(AuthGoogle.TESTER_EMAIL, '', ''))
			self.assertEqual(200, response.status_code)
			auth_token = response.get_json()
			header = {'Authorization': 'Bearer {}'.format(auth_token['access_token'])}
			response = client.get(URL + 'user/{}/'.format(self.tester_g_uuid), headers=header)
			self.assertEqual(200, response.status_code)
			# GET NON-EXISTENT PARTICIPANT
			response = client.get(URL_NOTIFICATION.format('NOT_VALID_USERID'), headers=header,
								  content_type='application/json')
			self.assertEqual(403, response.status_code)
			# VALID USER
			response = client.get(URL_NOTIFICATION.format(self.tester_g_uuid), headers=header,
								  content_type='application/json')
			self.assertEqual(200, response.status_code)
			u_notifications = response.get_json()['notifications']
			self.assertEqual(0, len(u_notifications))
