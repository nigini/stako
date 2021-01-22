import unittest
import settings

from pymongo import MongoClient
import mongo
from mongo import ExperimentMongo, APIMongo, UserSummary
from data import StakoActivity
from datetime import datetime, date

class TestStako(unittest.TestCase):

	def setUp(self):
		settings.MONGODB_NAME = settings.MONGODB_NAME_TEST
		client = MongoClient(settings.MONGODB_URL)
		db = client[settings.MONGODB_NAME_TEST]
		collection = db[mongo.COLLECTION_AUTH]
		collection.drop()
		collection = db[mongo.COLLECTION_USERS]
		collection.drop()
		collection = db[mongo.COLLECTION_ACTIVITIES]
		collection.drop()
		self.experiment = ExperimentMongo(settings)
		self.summary = UserSummary(settings)
		self.api = APIMongo(settings)


class TestExperiment(TestStako):

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


TESTER_EMAIL = 'user@tester.com'
TESTER_ACT1 = 'https://stackoverflow.com/questions/41051434/how-to-untrack-files-git-and-git-gui'
TESTER_ACT1_TAGS = ['git', 'git-gui']
TESTER_ACT2 = 'https://stackoverflow.com/questions/16819222/'
TESTER_ACT2_TAGS = ['python', 'python-3.x', 'list', 'dictionary', 'python-2.x']
TESTER_ACT3 = 'https://stackoverflow.com/questions/65474737/iteration-over-dictionary-keys-and-values'
TESTER_ACT3_TAGS = ['python', 'list', 'dictionary', 'iteration']


class TestActivitySummary(TestStako):

	def setUp(self):
		super(TestActivitySummary, self).setUp()
		self.TESTER_UUID = self.experiment.add_user(TESTER_EMAIL)
		# SHOULD NOT BE INCLUDED IN SUMMARY AS IT IS A CLICK NOT A VISIT
		test_activity = StakoActivity.get_empty_activity()
		test_activity['UUID'] = self.TESTER_UUID
		test_activity['URL'] = TESTER_ACT1
		test_activity['TYPE'] = StakoActivity.ACTIVITY_TYPE_SO_CLICK
		saved = self.api.save_activity(test_activity)
		self.assertTrue(saved)
		test_activity = StakoActivity.get_empty_activity()
		test_activity['UUID'] = self.TESTER_UUID
		test_activity['URL'] = TESTER_ACT2
		test_activity['TYPE'] = StakoActivity.ACTIVITY_TYPE_SO_VISIT
		saved = self.api.save_activity(test_activity)
		self.assertTrue(saved)
		test_activity = StakoActivity.get_empty_activity()
		test_activity['UUID'] = self.TESTER_UUID
		test_activity['URL'] = TESTER_ACT3
		test_activity['TYPE'] = StakoActivity.ACTIVITY_TYPE_SO_VISIT
		saved = self.api.save_activity(test_activity)
		self.assertTrue(saved)

	def test_visits_summary(self):
		current_timestamp = int(datetime.timestamp(datetime.utcnow()))
		current_iso_date = datetime.fromtimestamp(current_timestamp).isocalendar()
		current_year = str(current_iso_date[0])
		current_week = str(current_iso_date[1])

		test_u = self.api.get_user(self.TESTER_UUID)
		u_summary = test_u['activity']['weekly_summary']
		self.assertEqual(1, len(u_summary.keys()))
		self.assertTrue('1970' in u_summary.keys())
		self.assertTrue('1' in u_summary['1970'].keys())

		# TODO: Should use a Mock SO_API to make sure we have the intended data back
		updated = self.summary.update_user(self.TESTER_UUID)
		self.assertTrue(updated)
		test_u = self.api.get_user(self.TESTER_UUID)
		u_summary = test_u['activity']['weekly_summary']
		self.assertEqual(2, len(u_summary))
		self.assertTrue(current_year in u_summary.keys())
		self.assertTrue(current_week in u_summary[current_year].keys())
		self.assertEqual(2, u_summary[current_year][current_week]['pages_visited'])
		top_tags = u_summary[current_year][current_week]['top_tags']
		self.assertEqual(2, top_tags['python']['pages_visited'])
		self.assertEqual(2, top_tags['list']['pages_visited'])
		self.assertEqual(2, top_tags['dictionary']['pages_visited'])
		self.assertEqual(1, top_tags['python-3.x']['pages_visited'])
