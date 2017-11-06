import requests
import json
import constants

def authenticate_user(auth_params):
    print('authenticating')
    devise_response = requests.post(constants.STUY_SPEC_API_URL + '/auth',
                                    data=json.dumps(auth_params),
                                    headers={
                                        'Content-Type': 'application/json'
                                    })
    devise_response.raise_for_status()
    return devise_response.json().get('id', -1)

def update_user(user_id):
    print('update_user(%d) has not been completed' % user_id)