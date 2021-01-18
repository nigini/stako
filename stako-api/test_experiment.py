import unittest
import settings

from pymongo import MongoClient
import mongo
from mongo import ExperimentMongo, APIMongo


class TestExperiment(unittest.TestCase):

	def setUp(self):
		settings.MONGODB_NAME = settings.MONGODB_NAME_TEST
		client = MongoClient(settings.MONGODB_URL)
		db = client[settings.MONGODB_NAME_TEST]
		collection = db[mongo.COLLECTION_AUTH]
		collection.drop()
		collection = db[mongo.COLLECTION_USERS]
		collection.drop()
		self.experiment = ExperimentMongo(settings)
		self.api = APIMongo(settings)

	def test_experiment_user(self):
		response = self.experiment.get_user('non_participant@gmail.com')
		self.assertEqual({}, response)
		# ADD experiment user
		uuid = self.experiment.add_user('participant@gmail.com')
		self.assertRegex(uuid.lower(), "[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}")
		response = self.experiment.get_user('participant@gmail.com')
		self.assertEqual('participant@gmail.com', response['email'])
		self.assertEqual(uuid, response['uuid'])
		self.assertEqual([], response['roles'])
		# CREATED associated STAKO user (same UUID)
		stako_user = self.api.get_user(uuid)
		self.assertEqual(uuid, stako_user['uuid'])
		# FAIL to add existing user
		response = self.experiment.add_user('participant@gmail.com')
		self.assertIsNone(response)
