import unittest
import settings

from requests import get, put
from datetime import datetime
from pymongo import MongoClient
import json

from api import app, UserActivity
ACTIVITY_TYPE_SO_VISIT = UserActivity.ACTIVITY_TYPE_SO_VISIT
ACTIVITY_TYPE_SO_CLICK = UserActivity.ACTIVITY_TYPE_SO_CLICK

app.testing = True

URL = 'http://127.0.0.1:5000/v1/'
URL_ACTIVITY = URL + 'user/{}/activity/'


class TestUserAPI(unittest.TestCase):
	def setUp(self):
		client = MongoClient(settings.MONGODB_URL)
		db = client[settings.MONGODB_NAME_TEST]
		collection = db['users']
		collection.drop()

	def test_users_base(self):
		with app.test_client() as client:
			response = client.get(URL + 'user/1/')
			self.assertEqual(200, response.status_code)
			self.assertEqual({}, response.get_json())
			#CREATE NEW
			response = client.post(URL + 'user/')
			self.assertEqual(200, response.status_code)
			self.assertTrue('uuid' in response.get_json())
			uuid = response.get_json()['uuid']
			response = client.get(URL + 'user/{}/'.format(uuid))
			self.assertEqual(200, response.status_code)
			user = response.get_json()
			self.assertEqual(uuid, user['uuid'])
			self.assertTrue('nickname' in user)
			self.assertTrue('email' in user)
			self.assertTrue('motto' in user)
			self.assertTrue('activity' in user)
			self.assertTrue('communities' in user)
			self.assertTrue('start_date' in user)

	def test_users_get_by_any_key(self):
		with app.test_client() as client:
			#CREATE NEW
			response = client.post(URL + 'user/')
			self.assertEqual(200, response.status_code)
			self.assertTrue('uuid' in response.get_json())
			user = response.get_json()
			user['nickname'] = 'uTester'
			user['email'] = 'user@tester.com'
			user['motto'] = 'uTester will test it all!'
			user.pop('activity', None)
			user.pop('communities', None)
			response = client.put(URL + 'user/{}/'.format(user['uuid']), data=json.dumps(user), content_type='application/json')
			self.assertEqual(200, response.status_code)
			#SEARCH
			uuid = response.get_json()['uuid']
			email = response.get_json()['email']
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
			self.assertEqual(email, user['email'])
			#BY_EMAIL
			response = client.get(URL + 'user/?key={}&value={}'.format('email', email))
			self.assertEqual(200, response.status_code)
			user = response.get_json()
			self.assertEqual(uuid, user['uuid'])
			self.assertEqual(email, user['email'])

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
			user['email'] = 'user@tester.com'
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
			self.assertEqual(user['email'], user2['email'])
			self.assertEqual(user['motto'], user2['motto'])
			self.assertEqual(user['start_date'], user2['start_date'])
			self.assertTrue('activity' in user2)
			self.assertTrue('communities' in user2)
			# SHOULD NOT FIND USER
			wrong_uuid = 'SHOULD_NOT_EXIST'
			response = client.put(URL + 'user/{}/'.format(wrong_uuid), data=json.dumps(user2), content_type='application/json')
			self.assertEqual(404, response.status_code)

	def test_activity(self):
		with app.test_client() as client:
			an_activity = {'URL': 'https://stackoverflow.com/questions/20001229/',
						   'TYPE': ACTIVITY_TYPE_SO_VISIT}
			# NO USER
			response = client.post(URL_ACTIVITY.format('SOME_BROKEN_UUID'), data=json.dumps(an_activity),
									content_type='application/json')
			self.assertEqual(404, response.status_code)

			# Now with a real user
			response = client.post(URL + 'user/')
			self.assertEqual(200, response.status_code)
			uuid = response.get_json()['uuid']
			response = client.post(URL_ACTIVITY.format(uuid), data=json.dumps(an_activity),
									content_type='application/json')
			self.assertEqual(200, response.status_code)
			saved_activity = response.get_json()
			self.assertEqual(uuid, saved_activity['UUID'])
			self.assertEqual(an_activity['URL'], saved_activity['URL'])
			self.assertEqual(ACTIVITY_TYPE_SO_VISIT, saved_activity['TYPE'])

			# NO URL or TYPE
			a_bad_activity = {}
			response = client.post(URL_ACTIVITY.format(uuid), data=json.dumps(a_bad_activity),
									content_type='application/json')
			self.assertEqual(400, response.status_code)
			# BAD URL
			a_bad_activity = {'URL': 'stackoverflow.com'}
			response = client.post(URL_ACTIVITY.format(uuid), data=json.dumps(a_bad_activity),
									content_type='application/json')
			self.assertEqual(400, response.status_code)
			# MISSING ACTIVITY "TYPE"
			a_bad_activity = an_activity.copy()
			a_bad_activity.pop('TYPE', None)
			response = client.post(URL_ACTIVITY.format(uuid), data=json.dumps(a_bad_activity),
								   content_type='application/json')
			self.assertEqual(400, response.status_code)
			# NON-EXISTING ACTIVITY TYPE
			a_bad_activity['TYPE'] = 'NOT_VALID'
			response = client.post(URL_ACTIVITY.format(uuid), data=json.dumps(a_bad_activity),
								   content_type='application/json')
			self.assertEqual(400, response.status_code)

			# MISSING DATA FOR VALID TYPE
			another_activity = an_activity.copy()
			another_activity['TYPE'] = ACTIVITY_TYPE_SO_CLICK
			response = client.post(URL_ACTIVITY.format(uuid), data=json.dumps(another_activity),
								   content_type='application/json')
			self.assertEqual(400, response.status_code)
			# FIXING FOR click TYPE
			another_activity['ELEMENT'] = 'USER:1234'
			response = client.post(URL_ACTIVITY.format(uuid), data=json.dumps(another_activity),
								   content_type='application/json')
			self.assertEqual(200, response.status_code)



class Teams:#TestTeamsAPI(unittest.TestCase):

	def setUp(self):
		client = MongoClient(settings.MONGODB_URL)
		db = client[settings.MONGODB_NAME_TEST]
		collection = db['teams']
		collection.drop()

	def test_teams(self):
		with app.test_client() as client:
			response = client.get(URL + 'teams/test1;test2/')
			self.assertEqual(200, response.status_code)
			self.assertEqual({}, response.get_json())

			response = client.put(URL + 'teams/test1;test2/')
			self.assertEqual(200, response.status_code)
			response = client.get(URL + 'teams/test1;test2/')
			self.assertEqual(200, response.status_code)
			team = response.get_json()
			print(team)
			self.assertEqual('test1', team['tags'][0])
			self.assertEqual('test2', team['tags'][1])
			self.assertEqual(0, len(team['participants']))
			self.assertEqual(0, team['facts']['num_posts'])
			self.assertGreaterEqual(int(datetime.timestamp(datetime.utcnow())), team['last_updated'])
