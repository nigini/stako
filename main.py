import settings

from api import api_get_questions

from flask import Flask
from flask import render_template

app = Flask(__name__)

@app.route("/")
def hello():
    return "Hello World!"


@app.route("/team/<tags>")
def team(tags='python'):
	tags_list = tags.split(';')
	#TODO define and change this to TEAM entity!!!
	questions = get_questions(tags_list)
	if(len(questions) > 0):
		return render_template('team.html', tags=tags, questions=questions)
	return 'NO TAG TEAM WAS FOUND FOR: {}'.format(tags)


def get_questions(tag_list, size=10):
	#TODO turn into an API call to TEAMS
	questions = api_get_questions(tag_list, size)
	return questions