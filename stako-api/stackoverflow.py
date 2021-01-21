import settings
import requests

API_SO_QS = 'https://api.stackexchange.com/2.2/questions/{}?site=stackoverflow&key={}'


class Question:
    @staticmethod
    def get_questions(question_ids):
        if len(question_ids) > 0:
            ids_str = ''
            for q in question_ids:
                if q.isdigit():
                    ids_str += q+';'
            r_url = API_SO_QS.format(ids_str[:-1], settings.SO_API_KEY)
            response = requests.get(r_url)
            if response.status_code == 200:
                return response.json()['items']
        return {}

    @staticmethod
    def get_visits_questions_keys(qs):
        questions = {}
        for act in qs:
            url_s = act['URL'].split('/')
            if url_s[2].lower() == 'stackoverflow.com' and url_s[3].lower() == 'questions' and url_s[4].isdigit():
                questions[url_s[4]] = act
        return questions
