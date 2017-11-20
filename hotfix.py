import requests, json
media_response = requests.get('http://localhost:3000/media')
media = media_response.json()
for image in media:
  if type(image['media_type']) is not str:
    requests.put('http://localhost:3000/media/' + str(image['id']),
                 data=json.dumps({'media_type': 'photo'}),
                 headers={'Content-Type': 'application/json'})