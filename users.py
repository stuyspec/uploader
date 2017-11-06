import requests
import json
import constants

def authenticate_user(auth_params):
    print(4)
    print(auth_params)
    devise_response = requests.post(constants.STUY_SPEC_API_URL + '/auth',
                                    data=json.dumps(auth_params),
                                    headers={
                                        'Content-Type': 'application/json'
                                    })
    devise_response.raise_for_status()
    print(5)
    return devise_response.json().get('id', -1)

def update_user(user_id):
    print(user_id)