from datetime import datetime
import argparse
import sys
import pathlib
sys.path.append(pathlib.Path(__file__).parent.absolute().__str__() + '/..')
import stako.settings as settings
from stako.api.data.mongo import APIMongo, ExperimentMongo, UserSummary

api = APIMongo(settings)
exp = ExperimentMongo(settings)
sum = UserSummary(settings)


def add_user(user_email, role):
    # TODO: Check invalid email format
    uuid = exp.add_participant(user_email)
    if uuid:
        print("Added participant {}.".format(user_email))
        added = exp.add_participant_role(user_email, role)
        if added:
            print("Added role {} to participant {}.".format(role, user_email))
            pass_key = exp.regen_participant_passkey(user_email)
            print("And this is the participant's passkey: --> {} <--".format(pass_key))
        else:
            print("FAILED to add role {} to participant {}.".format(role, user_email))
    else:
        print("FAILED to add participant {}.".format(user_email))


def recreate_password(user_email):
    new_pass = exp.regen_participant_passkey(user_email)
    if new_pass:
        print("New participant passkey: --> {} <--".format(new_pass))
    else:
        print("FAILED to generate passkey. Is this a valid participant email?")


def update_summary_all(force_restart=False, timestamp=None):
    print("===========================================================")
    print("USERS UPDATE: {}".format(datetime.now()))
    print("===========================================================")
    accounts = exp.get_all()
    for a in accounts:
        update_summary(a['uuid'], force_restart, timestamp)


def update_summary(uuid, force_restart=False, timestamp=None):
    user = api.get_user(uuid)
    if not timestamp:
        timestamp = user['activity']['updated']
    result = sum.update_user(user['uuid'], force_restart, timestamp)
    print("Updated user {}: {}".format(user['uuid'], result))


# CLECK setting to verify what experiments are available.
def update_add_experiment(email, experiment_name, experiment_condition):
    result = exp.add_participant_experiment(email, experiment_name, experiment_condition)
    print("Participant added to experiment? {}".format(result))

parser = argparse.ArgumentParser(description='EXPERIMENT PARTICIPANTS MANAGEMENT SCRIPT')
subparsers = parser.add_subparsers(help='Commands', dest='command')

update_s_c = subparsers.add_parser('update_summary', help='Updates weekly activities summary.')
update_s_c.add_argument('--uuid', help='Updates the participant weekly activities with given UUID.')
update_s_c.add_argument('--all', action='store_true', help='Updates all participants weekly activities.')
update_s_c.add_argument('--refresh', action='store_true', help='Force recreating weekly activities.')
update_s_c.add_argument('--timestamp',
                      help='Updates summary with activities that happened after the UTC TIMESTAMP in seconds.')

create_c = subparsers.add_parser('create', help='Create new research participant')
create_c.add_argument('email', help='Email account used to authenticate user.')
create_c.add_argument('--role', help='A user role: [<participant>, researcher, tester].', default='participant')

update_c = subparsers.add_parser('update', help='Update participant')
update_c.add_argument('email', help='Email account used to authenticate user.')
update_c.add_argument('--passkey', action='store_true', help='Regenerate the participant\'s passkey.')
update_c.add_argument('--add_experiment', help='Add to experiment EXP_NAME::EXP_CONDITION (double colons required).')


args = parser.parse_args()
if args.command == 'create':
    add_user(args.email, args.role)
elif args.command == 'update':
    if args.passkey and args.email:
        recreate_password(args.email)
    elif args.add_experiment and args.email:
        experiment = args.add_experiment.split('::')
        if len(experiment) == 2:
            update_add_experiment(args.email, experiment[0], experiment[1])
        else:
            print('For <add_experiment>: specify EXP_NAME::EXP_CONDITION (double colons required).')
    else:
        print('For <UPDATE>, specify what you want to change.')
elif args.command == 'update_summary':
    if args.uuid:
        update_summary(args.uuid, args.refresh, args.timestamp)
    elif args.all:
        update_summary_all(args.refresh, args.timestamp)
    else:
        print('For <UPDATE_SUMMARY>, please provide a <UUID> or <ALL>!')
else:
    parser.print_help()
