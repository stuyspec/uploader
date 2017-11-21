from colorama import Fore, Back, Style

import requests
import json
import constants


def post_outquotes(article_data):
    for outquote in article_data['outquotes']:
        outquote_response = requests.post(
            constants.API_OUTQUOTES_ENDPOINT,
            data=json.dumps({
                'article_id': article_data['id'],
                'text': outquote.decode('utf-8')
            }),
            headers={
                'Content-Type': 'application/json'
            })
        outquote_response.raise_for_status()
    return article_data['id']
