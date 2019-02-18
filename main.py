import requests
import random
from flask_pymongo import PyMongo

from flask import Flask
from flask import render_template

app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://localhost:27017/qa-teams"
mongo = PyMongo(app)

@app.route("/")
def hello():
    return "Hello World!"


@app.route("/team/<tags>")
def team(tags='python'):
	#tags = ['python', 'tensorflow']
	tags_list = tags.split(';')
	questions = get_questions(tags_list)
	if(len(questions) > 0):
		return render_template('team.html', tags=tags, questions=questions)
	return 'NO TAG TEAM WAS FOUND FOR: {}'.format(tags)


# Returns a list of FAQ containing the tag_list 
# items info: ['tags', 'owner', 'is_answered', 'view_count', 
#              'protected_date', 'accepted_answer_id', 
#              'answer_count', 'score', 'last_activity_date', 
#              'creation_date', 'last_edit_date', 'question_id', 
#              'link', 'title']
def get_questions(tag_list,size=10):
	questions = mongo_get_questions(tag_list, size)
	if len(questions)>0:
		return questions
	else:
		questions = api_get_questions(tag_list)
		if len(questions)>0:
			mongo_save_questions(questions)
			return sample_list(questions, size)


def sample_list(my_list, size):
	if size < len(my_list):
		indexes = random.sample(range(len(my_list)), size)
		return [my_list[i] for i in indexes]
	else:
		return my_list


def mongo_get_questions(tag_list, size):
	collection = mongo.db['questions']
	result = collection.aggregate([
		{ '$match': { 'tags': tag_list } }, 
		{ '$sample': { 'size': size } } ])
	return list(result)


def api_get_questions(tag_list):
	#ToDo record search and avoid void ones for some time.
	tags_key = ';'.join(sorted(tag_list))
	#ToDo get this as parameter
	base_url = 'https://api.stackexchange.com/2.2/tags/{}/faq?site=stackoverflow'
	#ToDo authenticate
	url = base_url.format(tags_key)
	questions = requests.get(url)
	if questions.status_code == 200:
		return list(questions.json().items())[0][1]
	return []

def mongo_save_questions(questions_list):
	#ToDo test format
	collection = mongo.db['questions']
	collection.insert_many(questions_list)