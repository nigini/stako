import unittest
import settings

from requests import get, put
from datetime import datetime
from pymongo import MongoClient

from api import app
app.testing = True

URL = 'http://127.0.0.1:5000/v1/'


class TestTeamsAPI(unittest.TestCase):

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
