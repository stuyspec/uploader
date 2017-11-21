import requests

response = requests.post(
    'http://stuyspec-api-prod.us-east-1.elasticbeanstalk.com/media',
    files={'medium[attachment]': open('web.jpg', 'rb')},
    data={
        'medium[article_id]': 1,
        'medium[user_id]': 1,
    })
print(response)
response.raise_for_status()
