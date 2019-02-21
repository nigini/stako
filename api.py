import settings
import requests
import random

from mongo import mongo_save_questions, mongo_get_questions

# Returns a list of QUESTIONS containing the tag_list 
# items info: https://api.stackexchange.com/docs/types/question
def api_get_questions(tag_list, size=10):
	questions = mongo_get_questions(tag_list, size)
	if len(questions)>0:
		return questions
	else:
		questions = so_get_questions(tag_list)
		#TODO trigger GET_ANSWERS and GET_COMMENTS?
		if len(questions)>0:
			mongo_save_questions(questions) #Celery task
			return sample_list(questions, size)


def so_get_questions(tag_list):
	#TODO record search and avoid void ones for some time.
	tags_key = ';'.join(sorted(tag_list))
	#TODO get this as parameter?
	base_url = settings.API_SO_TAG_QS
	#TODO authenticate
	url = base_url.format(tags_key)
	questions = requests.get(url)
	if questions.status_code == 200:
		return list(questions.json().items())[0][1]
	return []


def sample_list(my_list, size):
	if size < len(my_list):
		indexes = random.sample(range(len(my_list)), size)
		return [my_list[i] for i in indexes]
	else:
		return my_list