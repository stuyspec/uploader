from colorama import Fore, Back, Style

import requests
import json
import constants

def post_outquotes(article_id, outquotes):
    for outquote in outquotes:
        outquote_response = requests.post(constants.API_OUTQUOTES_ENDPOINT,
                                          data=json.dumps({
                                              'article_id': article_id,
                                              'text': outquote.decode("utf-8")
                                          }),
                                          headers={
                                              'Content-Type':
                                                  'application/json'
                                          })
    return article_id
