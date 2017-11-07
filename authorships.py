import requests, json
import constants

def post_authorships(authorship_data):
    print(authorship_data)
    article_id, contributor_ids = authorship_data
    for c in contributor_ids:
        update_response = requests.post(constants.API_AUTHORSHIPS_ENDPOINT,
                                        data=json.dumps({
                                            'article_id': article_id,
                                            'user_id': c
                                        }),
                                        headers={
                                            'Content-Type': 'application/json'
                                        })
        update_response.raise_for_status()
        print('created authorship for %d' % c)
    return article_id
