from pymongo import MongoClient
from bson.json_util import loads, dumps
#from celery import Celery
#queue = Celery()


class APIMongo:

	def __init__(self, settings):
		self.client = MongoClient(settings.MONGODB_URL)
		self.db = self.client[settings.MONGODB_NAME]
		#queue = Celery('mongo', broker=settings.BROKER_URL)

#	@queue.task
	def save_questions(self, questions_list):
		#TODO test format
		collection = self.db['questions']
		#TODO check updates before creating new entries (QUESTIONID and LASTUPDATE?)
		collection.insert_many(questions_list)

	def get_questions(self, tag_list, size):
		collection = self.db['questions']
		# TODO Index collection by tags
		result = collection.aggregate([
			{'$match': {'tags': {'$all': tag_list}}},
			{'$sample': {'size': size}}])
		return list(result)

	def get_teams(self, tag_list):
		collection = self.db['teams']
		tag_list.sort()
		# TODO Index collection by tags
		result = collection.find({
			'tags': {
				'$size': len(tag_list),
				'$all': tag_list
			}}, {'_id': 0})
		return loads(dumps(result))

	def save_team(self, team):
		collection = self.db['teams']
		a_team = self._get_team(team['id'])
		if a_team is not None:
			a_team['last_updated'] = team['last_updated']
		else:
			a_team = team
		collection.save(a_team)

	def _get_team(self, team_id):
		collection = self.db['teams']
		return collection.find_one({'id': team_id})

#	@queue.task
	def save_message(self, message, channel='team_test'):
		pass