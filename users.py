from promise import Promise

import requests
import json
import constants, backups, utils

users = []
user_roles = []
roles = []

def init():
    """Initiates globals with API data"""
    global users, user_roles, roles
    users = requests.get(constants.API_USERS_ENDPOINT).json()
    user_roles = requests.get(constants.API_USER_ROLES_ENDPOINT).json()
    roles = requests.get(constants.API_ROLES_ENDPOINT).json()


def update_user(user_id, data):
    print('update_user(%d) has not been completed' % user_id, data)


def get_contributor_id(name):
    """Checks if contributor exists"""
    contributor_role_id = next(
        (r for r in roles if r['title'] == 'Contributor'),
        -1
    )
    return next((
        u for u in users
        if ('{firstname} {lastname}'.format(**u) == name
            and next((
               u_r for u_r in user_roles
               if (u_r['user_id'] == u['id']
                   and u_r['role_id'] == contributor_role_id)
            )) is not None)
    ), {}).get('id', -1)


def label_existing_contributors(contributors):
    """Returns contributors in the form [(name, contributor_id)]"""
    return [
        (c, get_contributor_id(c))
        for c in contributors
    ]


def authenticate_user(auth_params):
    devise_response = requests.post(constants.API_AUTH_ENDPOINT,
                                    data=json.dumps(auth_params),
                                    headers={
                                        'Content-Type': 'application/json'
                                    })
    devise_response.raise_for_status()
    return devise_response.json().get('id', -1)


def create_contributor(name):
    name = name.split(' ')
    if len(name) < 2: name *= 2  # first and last name are the same
    user_data = {
        'firstname': ' '.join(name[:-1]),
        'lastname': name[-1]

    }
    password = utils.generate_password(16)  # generates password of length 16
    auth_params = {
        'email': backups.get_email_by_name(name),
        'password': password,
        'password_confirmation': password,
    }
    create_contributor_promise = Promise(
        lambda resolve, reject: resolve(authenticate_user(auth_params))
    )\
        .then(lambda user_id: update_user(user_id, user_data))
    return create_contributor_promise.get()


def post_contributors(article_id, contributors):
    contributors = label_existing_contributors(contributors)
    contributor_ids = []

    for name, contributor_id in contributors:
        if contributor_id == -1:
            contributor_ids.append(create_contributor(name))
        else:
            contributor_ids.append(contributor_id)

    print(contributor_ids)

    return (
        article_id,
        contributor_ids
    )
