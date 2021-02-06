import sys
import os
sys.path.append(os.getcwd() + '/..')

import settings
from mongo import APIMongo, ExperimentMongo, UserSummary

api = APIMongo(settings)
exp = ExperimentMongo(settings)
sum = UserSummary(settings)

force_restart = False

#TESTERS
nigini = exp.get_user('nigini@gmail.com')
nigini_u = api.get_user(nigini['uuid'])

user = nigini_u
result = sum.update_user(user['uuid'], force_restart, user['activity']['updated'])

