from promise import Promise
from colorama import Fore, Back, Style
from slugify import slugify

import requests
import json
import constants, utils, main, config
import ast

users = []
user_roles = []
roles = []
backup_users = {}


def init():
    """Initiates globals with API data"""
    print('[0%] Loading users.\r'),  # comma lets next print overwrite.
    global users, user_roles, roles, backup_users, wp_users_dict
    users = requests.get(constants.API_USERS_ENDPOINT).json()
    user_roles = requests.get(constants.API_USER_ROLES_ENDPOINT).json()
    roles = requests.get(constants.API_ROLES_ENDPOINT).json()

    with open('backups/wp-users-backup.txt', 'r') as wp, \
            open('backups/drive-features-writers-2017-2018.txt', 'r') \
                    as features, \
            open('backups/drive-opinions-writers-2017-2018.txt', 'r') \
                    as opinions, \
            open('backups/drive-news-writers-2016-2017.txt', 'r') as news, \
            open('backups/drive-art-2016-2017.txt', 'r') as art:
        for user in ast.literal_eval(wp.read()).values() \
                    + ast.literal_eval(features.read()) \
                    + ast.literal_eval(opinions.read()) \
                    + ast.literal_eval(news.read()) \
                    + ast.literal_eval(art.read()):
            key = user['first_name'] + '+' + user['last_name']
            if key in backup_users:
                backup_users[key].append(user)
            else:
                backup_users[key] = [user]
    print('[100%] Loaded users.')


def get_email_by_name(name_dict):
    key = name_dict['first_name'] + '+' + name_dict['last_name']
    if key in backup_users:
        return backup_users[key][0][
            'email']  # shoudl give choices between all.
    for user in users:
        if (name_dict['first_name'] == user['first_name']
                and name_dict['last_name'] == user['last_name']):
            return user['email']
    raise LookupError('No email found for {first_name} {last_name}.'
                      .format(**name_dict))


def update_user(user_id, data):
    update_response = requests.put(
        constants.API_USERS_ENDPOINT + '/{}'.format(user_id),
        data=json.dumps(data),
        headers=config.headers)
    update_response.raise_for_status()
    main.updateHeaders(update_response)
    updated_user_json = update_response.json()
    global users
    users.append(updated_user_json)
    return updated_user_json.get('id', -1)


def get_role_id_by_name(role_name):
    try:
        return next((r for r in roles if r['title'] == role_name))['id']
    except StopIteration:
        raise ValueError('Role {} does not exist.'.format(role_name))
    except KeyError:
        raise ValueError('Role {} exists but has no "id" key.'.format(role_name))


def make_user_role(user_id, role_name):
    role_id = get_role_id_by_name(role_name)

    user_role_response = requests.post(
        constants.API_USER_ROLES_ENDPOINT,
        data=json.dumps({
            'user_id': user_id,
            'role_id': role_id
        }),
        headers=config.headers)
    user_role_response.raise_for_status()
    main.updateHeaders(user_role_response)
    user_role_json = user_role_response.json()
    global user_roles
    user_roles.append(user_role_json)
    return user_id


def get_contributor_id(name):
    """Checks if contributor exists."""
    contributor_role_id = get_role_id_by_name('Contributor')
    output = -1 # user does not exist, user_role does not exist
    for u in users:
        if '{first_name} {last_name}'.format(**u).strip() == name:
            output = str(u['id'])
            if next((user_role for user_role in user_roles
                if (user_role['user_id'] == u['id']
                    and user_role['role_id'] == contributor_role_id)), None):
                return u['id']
            break
    return output


def authenticate_new_user(name_dict):
    try:
        email = get_email_by_name(name_dict)
    except LookupError:
        email = ''
        while email == '':
            email = raw_input(
                (Fore.RED + Style.BRIGHT + 'no email found for ' +
                 '{first_name} {last_name}. '.format(**name_dict) + 'email: ' +
                 Style.RESET_ALL))
    password = utils.generate_password(16)  # generates password of length 16
    auth_params = {
        'email': email,
        'password': password,
        'password_confirmation': password,
    }
    devise_response = requests.post(
        constants.API_AUTH_ENDPOINT,
        data=json.dumps(auth_params),
        headers=config.headers)
    devise_response.raise_for_status()
    main.updateHeaders(devise_response)
    print(Fore.YELLOW + Style.BRIGHT +
          'Authenticated new user with e-mail {}.'.format(email) +
          Style.RESET_ALL)
    return devise_response.json().get('data', {}).get('id', -1)


def name_to_dict(name):
    name = name.split(' ')
    if len(name) < 2: name *= 2  # first and last name are the same
    return {'first_name': ' '.join(name[:-1]), 'last_name': name[-1]}


def create_contributor(name):
    name_dict = utils.merge_two_dicts(
        name_to_dict(name), {
            'slug': slugify(name)
        })

    create_contributor_promise = Promise(
        lambda resolve, reject: resolve(authenticate_new_user(name_dict))
    )\
        .then(lambda user_id: update_user(user_id, name_dict))\
        .then(lambda user_id: make_user_role(user_id, 'Contributor'))\
        .then(lambda user_id: user_id)
    return create_contributor_promise.get()


def get_artist_id(name, role_name):
    role_id = get_role_id_by_name(role_name)
    output = 0
    for u in users:
        if '{first_name} {last_name}'.format(**u).strip() == name:
            output = -u['id']
            if next(
                (user_role for user_role in user_roles
                 if (user_role['user_id'] == u['id']
                     and user_role['role_id'] == role_id)), None) is not None:
                return u['id']
            break
    return output


def create_artist(name, art_type):
    name_dict = utils.merge_two_dicts(
        name_to_dict(name), {
            'slug': slugify(name)
        })

    if art_type.lower() == 'illustration':
        role_name = 'Illustrator'
    elif art_type.lower() == 'photo':
        role_name = 'Photographer'
    else:
        raise ValueError('Art type {} is not permitted.'.format(art_type))
    artist_id = get_artist_id(name, role_name)

    if artist_id == 0:  # user and user_role do not exist
        create_artist_promise = Promise(
            lambda resolve, reject: resolve(authenticate_new_user(name_dict))
        ) \
            .then(lambda user_id: update_user(user_id, name_dict)) \
            .then(lambda user_id: make_user_role(user_id, role_name)) \
            .then(lambda user_id: user_id)
        artist_id = create_artist_promise.get()
        print(Fore.YELLOW + Style.BRIGHT + 'Created {} #{}: {}.'
              .format(role_name, artist_id, name) + Style.RESET_ALL)

    elif artist_id < 0:  # user exists, but not user_role
        user_id = make_user_role(-artist_id, role_name)
        print(Fore.YELLOW + Style.BRIGHT + 'Made user #{}, {}, a {}.'
              .format(user_id, name, role_name) + Style.RESET_ALL)

    else:  # stuff exists
        print(Fore.YELLOW + Style.BRIGHT + 'Confirmed {} #{}: {}.'
              .format(role_name, artist_id, name) + Style.RESET_ALL)

    return artist_id


def post_contributors(article_data):
    article_id, contributors = [article_data[key] for key in ['id', 'contributors']]
    contributor_ids = []
    for name, contributor_id in [(c, get_contributor_id(c)) for c in contributors]:
        if contributor_id == -1: # -1: no user, no user_role
            new_contributor_id = create_contributor(name)
            contributor_ids.append(new_contributor_id)
            print(Fore.YELLOW + Style.BRIGHT + 'Created Contributor #{}: {}.'
                  .format(new_contributor_id, name) + Style.RESET_ALL)
        elif type(contributor_id) is str: # str: no user, but found user_role
            make_user_role(int(contributor_id), 'Contributor')
            print(Fore.YELLOW + Style.BRIGHT + 'Made User #{} a Contributor.'
                  .format(contributor_id) + Style.RESET_ALL)
        else: # positive integer: found both user and user-role
            contributor_ids.append(contributor_id)
            print(Fore.YELLOW + Style.BRIGHT + 'Confirmed Contributor #{}: {}.'
                  .format(contributor_id, name) + Style.RESET_ALL)
    return (article_id, contributor_ids)
