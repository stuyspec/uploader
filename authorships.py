import requests, json
import constants, main, config


def post_authorships(authorship_data):
    article_id, contributor_ids = authorship_data
    for c in contributor_ids:
        update_response = requests.post(
            constants.API_AUTHORSHIPS_ENDPOINT,
            data=json.dumps({
                'article_id': article_id,
                'user_id': c
            }),
            headers=config.headers)
        update_response.raise_for_status()
        main.updateHeaders(update_response)
    return article_id
