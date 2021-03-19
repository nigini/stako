STAKO_TEST = False
STAKO_DEBUG = False
STAKO_OAUTH_ID = ['']
STAKO_JWT_SECRET = 'ABCDEEFGHIJ1234567890'
STAKO_JWT_TOKEN_EXPIRES = 24*60*60

STAKO_EXPERIMENTS = {
    "test": ['group_a', 'group_b', 'control']
}

MONGODB_URL = 'mongodb://localhost:27017/'
MONGODB_NAME = 'qa-teams'
MONGODB_NAME_TEST = 'qa-teams-test'
BROKER_URL = 'amqp://localhost:5672'

SO_API_KEY = '1234567890'