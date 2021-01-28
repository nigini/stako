import unittest
import settings

from requests import get, put
from datetime import datetime
from pymongo import MongoClient
import mongo
from mongo import ExperimentMongo
from data import StakoActivity
import json

from api import app, Auth
ACTIVITY_TYPE_SO_VISIT = StakoActivity.ACTIVITY_TYPE_SO_VISIT
ACTIVITY_TYPE_SO_CLICK = StakoActivity.ACTIVITY_TYPE_SO_CLICK

app.testing = True

URL = 'http://127.0.0.1:5000/v1/'
URL_ACTIVITY = URL + 'user/{}/activity/'
TESTER_EMAIL = 'user@tester.com'


class TestAPI(unittest.TestCase):
	def setUp(self):
		settings.MONGODB_NAME = settings.MONGODB_NAME_TEST
		client = MongoClient(settings.MONGODB_URL)
		db = client[settings.MONGODB_NAME_TEST]
		users = db[mongo.COLLECTION_USERS]
		users.drop()
		activities = db[mongo.COLLECTION_ACTIVITIES]
		activities.drop()
		experiment = db[mongo.COLLECTION_AUTH]
		experiment.drop()
		experiment_mongo = ExperimentMongo(settings)
		self.tester_uuid = experiment_mongo.add_user(TESTER_EMAIL)


class TestAuthAPI(TestAPI):
	def test_auth(self):
		with app.test_client() as client:
			# NO EMAIL, NO GOOGLE_ID, NOR TOKEN
			response = client.get(URL + 'auth/')
			self.assertEqual(400, response.status_code)
			# INVALID EMAIL, GOOGLE_ID, AND TOKEN
			response = client.get(URL + 'auth/?email={}&google_id={}&token={}'.format('', '', ''))
			self.assertEqual(401, response.status_code)
			# TODO: VALID EMAIL, GOOGLE_ID, AND TOKEN


class TestUserAPI(TestAPI):
	def test_users_base(self):
		with app.test_client() as client:
			response = client.get(URL + 'user/1/')
			self.assertEqual(200, response.status_code)
			self.assertEqual({}, response.get_json())
			#CREATE NEW
			# TODO: Only Researchers should be able to call POST!
			response = client.post(URL + 'user/')
			self.assertEqual(200, response.status_code)
			self.assertTrue('uuid' in response.get_json())
			uuid = response.get_json()['uuid']
			response = client.get(URL + 'user/{}/'.format(uuid))
			self.assertEqual(200, response.status_code)
			user = response.get_json()
			self.assertEqual(uuid, user['uuid'])
			self.assertTrue('nickname' in user)
			self.assertFalse('email' in user)
			self.assertTrue('motto' in user)
			self.assertTrue('activity' in user)
			self.assertTrue('start_date' in user)

	def test_users_get_by_any_key(self):
		with app.test_client() as client:
			#CREATE NEW
			response = client.post(URL + 'user/')
			self.assertEqual(200, response.status_code)
			self.assertTrue('uuid' in response.get_json())
			user = response.get_json()
			user['nickname'] = 'uTester'
			user['motto'] = 'uTester will test it all!'
			user.pop('activity', None)
			response = client.put(URL + 'user/{}/'.format(user['uuid']), data=json.dumps(user), content_type='application/json')
			self.assertEqual(200, response.status_code)
			#SEARCH
			uuid = response.get_json()['uuid']
			##MALFORMED REQUEST
			response = client.get(URL + 'user/')
			self.assertEqual(400, response.status_code)
			response = client.get(URL + 'user/?key={}'.format('uuid'))
			self.assertEqual(400, response.status_code)
			response = client.get(URL + 'user/?value={}'.format(uuid))
			self.assertEqual(400, response.status_code)
			##NON-EXISTENT KEY
			response = client.get(URL + 'user/?key={}&value={}'.format('NON_EXISTENT', uuid))
			self.assertEqual(400, response.status_code)
			##NON-EXISTENT VALUE
			response = client.get(URL + 'user/?key={}&value={}'.format('uuid', 'NON_EXISTENT'))
			self.assertEqual(404, response.status_code)

			##BY UUID
			response = client.get(URL + 'user/?key={}&value={}'.format('uuid', uuid))
			self.assertEqual(200, response.status_code)
			user = response.get_json()
			self.assertEqual(uuid, user['uuid'])
			#BY_EMAIL
			#NON_AUTHORIZED
			response = client.get(URL + 'user/?key={}&value={}'.format('email', 'no_a_user@tester.com'))
			self.assertEqual(403, response.status_code)
			#AUTHORIZED
			response = client.get(URL + 'user/?key={}&value={}'.format('email', TESTER_EMAIL))
			self.assertEqual(200, response.status_code)
			user = response.get_json()
			self.assertEqual(self.tester_uuid, user['uuid'])

	def test_users_update(self):
		with app.test_client() as client:
			response = client.post(URL + 'user/')
			self.assertEqual(200, response.status_code)
			uuid = response.get_json()['uuid']
			response = client.get(URL + 'user/{}/'.format(uuid))
			self.assertEqual(200, response.status_code)
			# CHANGING USER DATA
			user = response.get_json()
			user['nickname'] = 'uTester'
			user['motto'] = 'uTester will test it all!'
			user['uuid'] = 'SHOULD_NOT_BE_CHANGED'
			user.pop('activity', None)
			user.pop('communities', None)
			response = client.put(URL + 'user/{}/'.format(uuid), data=json.dumps(user), content_type='application/json')
			self.assertEqual(200, response.status_code)
			# DID IT REALLY CHANGE?
			response = client.get(URL + 'user/{}/'.format(uuid))
			self.assertEqual(200, response.status_code)
			user2 = response.get_json()
			self.assertEqual(uuid, user2['uuid'])
			self.assertEqual(user['nickname'], user2['nickname'])
			self.assertEqual(user['motto'], user2['motto'])
			self.assertEqual(user['start_date'], user2['start_date'])
			self.assertTrue('activity' in user2)
			# SHOULD NOT FIND USER
			wrong_uuid = 'SHOULD_NOT_EXIST'
			response = client.put(URL + 'user/{}/'.format(wrong_uuid), data=json.dumps(user2), content_type='application/json')
			self.assertEqual(404, response.status_code)


class TestActivityAPI(TestAPI):
	def test_activity(self):
		with app.test_client() as client:
			# TODO: Test for all supported activity types!
			an_activity = {
				'url': 'https://stackoverflow.com/questions/20001229/',
				'type': ACTIVITY_TYPE_SO_VISIT
			}
			# NO USER
			response = client.post(URL_ACTIVITY.format('SOME_BROKEN_UUID'), data=json.dumps(an_activity),
									content_type='application/json')
			self.assertEqual(404, response.status_code)

			# Now with a real user
			response = client.post(URL_ACTIVITY.format(self.tester_uuid), data=json.dumps(an_activity),
									content_type='application/json')
			self.assertEqual(200, response.status_code)
			saved_activity = response.get_json()
			self.assertEqual(self.tester_uuid, saved_activity['uuid'])
			self.assertEqual(an_activity['url'], saved_activity['url'])
			self.assertEqual(ACTIVITY_TYPE_SO_VISIT, saved_activity['type'])

			# NO URL or TYPE
			a_bad_activity = {}
			response = client.post(URL_ACTIVITY.format(self.tester_uuid), data=json.dumps(a_bad_activity),
									content_type='application/json')
			self.assertEqual(400, response.status_code)
			# BAD URL
			a_bad_activity = {'url': 'stackoverflow.com'}
			response = client.post(URL_ACTIVITY.format(self.tester_uuid), data=json.dumps(a_bad_activity),
									content_type='application/json')
			self.assertEqual(400, response.status_code)
			# MISSING ACTIVITY "TYPE"
			a_bad_activity = an_activity.copy()
			a_bad_activity.pop('type', None)
			response = client.post(URL_ACTIVITY.format(self.tester_uuid), data=json.dumps(a_bad_activity),
								   content_type='application/json')
			self.assertEqual(400, response.status_code)
			# NON-EXISTING ACTIVITY TYPE
			a_bad_activity['type'] = 'NOT_VALID'
			response = client.post(URL_ACTIVITY.format(self.tester_uuid), data=json.dumps(a_bad_activity),
								   content_type='application/json')
			self.assertEqual(400, response.status_code)

			# MISSING DATA FOR VALID TYPE
			another_activity = an_activity.copy()
			another_activity['type'] = ACTIVITY_TYPE_SO_CLICK
			response = client.post(URL_ACTIVITY.format(self.tester_uuid), data=json.dumps(another_activity),
								   content_type='application/json')
			self.assertEqual(400, response.status_code)
			# FIXING FOR click TYPE
			another_activity['element'] = 'USER:1234'
			response = client.post(URL_ACTIVITY.format(self.tester_uuid), data=json.dumps(another_activity),
								   content_type='application/json')
			self.assertEqual(200, response.status_code)
