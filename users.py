from main import STUY_SPEC_API_URL
import requests
import json

def authenticate_user(auth_params):
    devise_response = requests.post(STUY_SPEC_API_URL + '/users',
                                    data=json.dumps(auth_params),
                                    headers={
                                        'Content-Type': 'application/json'
                                    })
    devise_response.raise_for_status()
    return devise_response.json().get('id', -1)