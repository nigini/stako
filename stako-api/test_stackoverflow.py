import unittest
import settings

from pymongo import MongoClient
import mongo
from mongo import ExperimentMongo, APIMongo
from data import StakoActivity
from stackoverflow import Question

TESTER_EMAIL = 'user@tester.com'
TESTER_ACT1 = 'https://stackoverflow.com/questions/41051434/how-to-untrack-files-git-and-git-gui'
TESTER_ACT1_TAGS = ['git', 'git-gui']
TESTER_ACT2 = 'https://stackoverflow.com/questions/16819222/'
TESTER_ACT2_TAGS = ['python', 'python-3.x', 'list', 'dictionary', 'python-2.x']
TESTER_ACT3 = 'https://stackoverflow.com/questions/65474737/iteration-over-dictionary-keys-and-values'
TESTER_ACT3_TAGS = ['python', 'list', 'dictionary', 'iteration']


class TestStackOverflow(unittest.TestCase):

	def setUp(self):
		settings.MONGODB_NAME = settings.MONGODB_NAME_TEST
		client = MongoClient(settings.MONGODB_URL)
		db = client[settings.MONGODB_NAME_TEST]
		users = db[mongo.COLLECTION_USERS]
		users.drop()
		self.activities = db[mongo.COLLECTION_ACTIVITIES]
		self.activities.drop()
		experiment = db[mongo.COLLECTION_AUTH]
		experiment.drop()
		experiment_mongo = ExperimentMongo(settings)
		self.TESTER_UUID = experiment_mongo.add_user(TESTER_EMAIL)
		self.api = APIMongo(settings)

	def test_get_question(self):
		q_ids = ['41051434', '16819222']
		so_questions = Question.get_questions(q_ids)
		self.assertEqual(2, len(so_questions))
		for key in so_questions.keys():
			self.assertTrue(key in q_ids)
		for tag in so_questions[q_ids[0]]['tags']:
			self.assertTrue(tag in TESTER_ACT1_TAGS)
		for tag in so_questions[q_ids[1]]['tags']:
			self.assertTrue(tag in TESTER_ACT2_TAGS)


	def test_get_visits(self):
		user_act = self.activities.find_one({'UUID': self.TESTER_UUID}, {'_id': 0})
		self.assertIsNone(user_act)

		test_activity = StakoActivity.get_empty_activity()
		test_activity['UUID'] = self.TESTER_UUID
		test_activity['URL'] = TESTER_ACT1
		test_activity['TYPE'] = StakoActivity.ACTIVITY_TYPE_SO_VISIT
		saved = self.api.save_activity(test_activity)
		self.assertTrue(saved)
		user_act = self.activities.find_one({'UUID': self.TESTER_UUID}, {'_id': 0})
		self.assertEqual(TESTER_ACT1, user_act['URL'])

		user_acts = self.activities.find({'UUID': self.TESTER_UUID}, {'_id': 0})
		response = list(Question.get_visits_questions_keys(user_acts).keys())
		self.assertEqual(1, len(response))
		self.assertEqual('41051434', response[0])

		test_activity = StakoActivity.get_empty_activity()
		test_activity['UUID'] = self.TESTER_UUID
		test_activity['URL'] = TESTER_ACT2
		test_activity['TYPE'] = StakoActivity.ACTIVITY_TYPE_SO_VISIT
		saved = self.api.save_activity(test_activity)
		self.assertTrue(saved)

		# SHOULD NOT BE INCLUDED AS THIS IS A CLICK NOT A VISIT
		test_activity = StakoActivity.get_empty_activity()
		test_activity['UUID'] = self.TESTER_UUID
		test_activity['URL'] = TESTER_ACT3
		test_activity['TYPE'] = StakoActivity.ACTIVITY_TYPE_SO_CLICK
		saved = self.api.save_activity(test_activity)
		self.assertTrue(saved)

		user_acts = self.activities.find({'UUID': self.TESTER_UUID}, {'_id': 0})
		response = list(Question.get_visits_questions_keys(user_acts).keys())
		self.assertEqual(2, len(response))
		self.assertEqual('41051434', response[0])
		self.assertEqual('16819222', response[1])
