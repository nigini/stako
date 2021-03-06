import unittest
import settings
import logging

from pymongo import MongoClient
import mongo
from mongo import ExperimentMongo, APIMongo, UserSummary
import data
from data import StakoActivity
from datetime import datetime, timedelta, timezone


class TestStako(unittest.TestCase):

	def setUp(self):
		logging.basicConfig(level=logging.INFO)
		settings.STAKO_TEST = True
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
# This CONF should match the MOCK DATA on the test_stakoverflow.json file!
TESTER_ACT1 = 'https://stackoverflow.com/questions/41051434/how-to-untrack-files-git-and-git-gui'
TESTER_ACT1_TAGS = ['git', 'git-gui']
TESTER_ACT2 = 'https://stackoverflow.com/questions/16819222/'
TESTER_ACT2_TAGS = ['python', 'python-3.x', 'list', 'dictionary', 'python-2.x']
TESTER_ACT3 = 'https://stackoverflow.com/questions/65474737/iteration-over-dictionary-keys-and-values'
TESTER_ACT3_TAGS = ['python', 'list', 'dictionary', 'iteration']


class TestActivitySummary(TestStako):

	def setUp(self):
		super(TestActivitySummary, self).setUp()
		self.today = datetime.utcnow().replace(tzinfo=timezone.utc)
		self.yesterday = self.today - timedelta(1)
		self.today0 = self.today.replace(hour=0, minute=0, second=0, microsecond=0)
		self.yesterday0 = self.today0 - timedelta(1)
		self.TESTER_UUID = self.experiment.add_user(TESTER_EMAIL)
		# SHOULD NOT BE INCLUDED IN SUMMARY AS IT IS A CLICK NOT A VISIT
		test_activity = StakoActivity.get_empty_activity()
		test_activity['uuid'] = self.TESTER_UUID
		test_activity['url'] = TESTER_ACT1
		test_activity['type'] = StakoActivity.ACTIVITY_TYPE_SO_CLICK
		saved = self.api.save_activity(test_activity)
		self.assertTrue(saved)
		test_activity = StakoActivity.get_empty_activity()
		test_activity['uuid'] = self.TESTER_UUID
		test_activity['url'] = TESTER_ACT2
		test_activity['type'] = StakoActivity.ACTIVITY_TYPE_SO_VISIT
		test_activity['timestamp'] = int(self.today.timestamp())
		saved = self.api.save_activity(test_activity)
		self.assertTrue(saved)
		test_activity = StakoActivity.get_empty_activity()
		test_activity['uuid'] = self.TESTER_UUID
		test_activity['url'] = TESTER_ACT3
		test_activity['type'] = StakoActivity.ACTIVITY_TYPE_SO_VISIT
		test_activity['timestamp'] = int(self.yesterday.timestamp())
		saved = self.api.save_activity(test_activity)
		self.assertTrue(saved)

	def test_visits_summary(self):
		teststart_tm = int(self.today.timestamp())
		today_iso_date = self.today.isocalendar()
		today_year = str(today_iso_date[0])
		today_week = str(today_iso_date[1])
		yesterday_iso_date = self.yesterday.isocalendar()
		yesterday_year = str(yesterday_iso_date[0])
		yesterday_week = str(yesterday_iso_date[1])

		test_u = self.api.get_user(self.TESTER_UUID)
		u_summary = test_u['activity']['weekly_summary']
		self.assertEqual(1, len(u_summary.keys()))
		self.assertTrue('1970' in u_summary.keys())
		self.assertTrue('1' in u_summary['1970'].keys())

		#GETS ACTIVITY FROM TODAY AND NO RESET (SUMMARY IS EMPTY ANYWAYS)
		updated = self.summary.update_user(self.TESTER_UUID, False, int(self.today0.timestamp()))
		self.assertTrue(updated)
		test_u = self.api.get_user(self.TESTER_UUID)
		self.assertTrue(test_u['activity']['updated'] >= teststart_tm)
		u_summary = test_u['activity']['weekly_summary']
		self.assertEqual(2, len(u_summary))
		self.assertTrue(today_year in u_summary.keys())
		self.assertTrue(today_week in u_summary[today_year].keys())
		self.assertEqual(1, u_summary[today_year][today_week]['pages_visited'])
		top_tags = u_summary[today_year][today_week]['top_tags']
		self.assertEqual(1, top_tags['python']['pages_visited'])
		self.assertEqual(1, top_tags['list']['pages_visited'])
		self.assertEqual(1, top_tags['dictionary']['pages_visited'])
		self.assertEqual(1, top_tags['python-3.x']['pages_visited'])
		self.assertEqual(1, top_tags['python-2.x']['pages_visited'])
		self.assertIsNone(top_tags.get('git'))

		#GETS ACTIVITY FROM TODAY AND YESTERDAY AND NO RESET
		updated = self.summary.update_user(self.TESTER_UUID, False, int(self.yesterday0.timestamp()))
		self.assertTrue(updated)
		test_u = self.api.get_user(self.TESTER_UUID)
		self.assertTrue(test_u['activity']['updated'] >= teststart_tm)
		u_summary = test_u['activity']['weekly_summary']
		self.assertEqual(2, len(u_summary))
		self.assertTrue(today_year in u_summary.keys())
		self.assertTrue(yesterday_year in u_summary.keys())
		self.assertTrue(today_week in u_summary[today_year].keys())
		self.assertTrue(yesterday_week in u_summary[yesterday_year].keys())
		# TODO These will fail if YEAR OR WEEK for TODAY and YESTERDAY are different!
		self.assertEqual(3, u_summary[today_year][today_week]['pages_visited'])
		top_tags = u_summary[today_year][today_week]['top_tags']
		self.assertEqual(3, top_tags['python']['pages_visited'])
		self.assertEqual(3, top_tags['list']['pages_visited'])
		self.assertEqual(3, top_tags['dictionary']['pages_visited'])
		self.assertEqual(2, top_tags['python-3.x']['pages_visited'])
		self.assertEqual(2, top_tags['python-2.x']['pages_visited'])
		self.assertEqual(1, top_tags['iteration']['pages_visited'])
		self.assertIsNone(top_tags.get('git'))


		#RESETS AND GETS ALL ACTIVITY
		updated = self.summary.update_user(self.TESTER_UUID, True)
		self.assertTrue(updated)
		test_u = self.api.get_user(self.TESTER_UUID)
		self.assertTrue(test_u['activity']['updated'] >= teststart_tm)
		u_summary = test_u['activity']['weekly_summary']
		self.assertEqual(2, len(u_summary))
		self.assertTrue(today_year in u_summary.keys())
		self.assertTrue(today_week in u_summary[today_year].keys())
		# TODO These will fail if YEAR OR WEEK for TODAY and YESTERDAY are different!
		self.assertEqual(2, u_summary[today_year][today_week]['pages_visited'])
		top_tags = u_summary[today_year][today_week]['top_tags']
		self.assertEqual(2, top_tags['python']['pages_visited'])
		self.assertEqual(2, top_tags['list']['pages_visited'])
		self.assertEqual(2, top_tags['dictionary']['pages_visited'])
		self.assertEqual(1, top_tags['python-3.x']['pages_visited'])
