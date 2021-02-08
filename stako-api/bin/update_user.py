import sys
import os
from datetime import datetime

sys.path.append(os.getcwd() + '/..')
import settings
from mongo import APIMongo, ExperimentMongo, UserSummary

api = APIMongo(settings)
exp = ExperimentMongo(settings)
sum = UserSummary(settings)

# TODO: Add command line argument to force restart for specific user
force_restart = False


def update_all():
    accounts = exp.get_all()
    for a in accounts:
        user = api.get_user(a['uuid'])
        result = sum.update_user(user['uuid'], force_restart, user['activity']['updated'])
        print("Updated user {}: {}".format(user['uuid'], result))


print("===========================================================")
print("USERS UPDATE: {}".format(datetime.now()))
print("===========================================================")
update_all()
