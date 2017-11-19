from apiclient import discovery
from apiclient.http import MediaIoBaseDownload
from pyfiglet import figlet_format
from PIL import Image
import httplib2
import requests
from slugify import slugify

import os
import re
import io

import constants

files = []
drive_service = None


def init(credentials):
    http = credentials.authorize(httplib2.Http())
    global drive_service
    drive_service = discovery.build('drive', 'v3', http=http)

    print('\n')
    print(figlet_format('SPEC CLI', font='slant'))

    if not os.path.exists('/tmp'):
        os.makedirs('/tmp')

    global files
    page_token = None
    while 1:
        response = drive_service.files().list(
            q="(mimeType='application/vnd.google-apps.folder'"
              + " or mimeType='application/vnd.google-apps.document'"
              + " or mimeType='application/pdf'"
              + " or mimeType contains 'image')"
              + " and not trashed",
            spaces='drive',
            fields='nextPageToken, files(id, name, parents, mimeType)',
            pageToken=page_token
        ).execute()
        files += response.get('files', [])
        page_token = response.get('nextPageToken', None)
        if page_token is None:
            print('[100%] Loaded {} Drive files.'.format(len(files)))
            return
        print('Loaded {} Drive files.'.format(len(files)))


def get_file(name_pattern, file_type, parent_id=None):
    if file_type in ['folder', 'document']:
        mime_type = 'application/vnd.google-apps.' + file_type
    else:
        mime_type = file_type
    if parent_id:
        return next((
            f for f in files if (f['mimeType'] == mime_type and
                                 re.match(name_pattern, f['name']) and
                                 parent_id in f.get('parents', [None]))
        ))
    return next((
        f for f in files if (f['mimeType'] == mime_type and
                             re.match(name_pattern, f['name']))
    ))


def get_children(parent_ids, file_type=None):
    if type(parent_ids) is unicode or type(parent_ids) is str:
        parent_ids = [parent_ids]
    if file_type is not None:
        if file_type in ['document', 'folder']:
            mime_type = 'application/vnd.google-apps.' + file_type
        elif file_type == 'image':
            mime_type = 'image'
        else:
            raise ValueError('Expected file type document, folder, image, but received: {}.'.format(file_type))
        return [
            f for f in files if (mime_type in f['mimeType'] and
                                 any(p in f.get('parents', [])
                                     for p in parent_ids))
        ]
    return [
        f for f in files if any(p in f.get('parents', [])
                                     for p in parent_ids)
    ]


def download_document(file):
    if file['mimeType'] != 'application/vnd.google-apps.document':
        raise ValueError('File of MIME type {} should not be downloaded here.'
                         .format(file['mimeType']))
    request = drive_service.files().export_media(
        fileId=file['id'], mimeType='text/plain')
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
        print('%d%%' % int(status.progress() * 100))

    return fh.getvalue()

def download_file(file):
    file_id = file['id']
    request = drive_service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
        print('Download {} {}%.'.format(file['name'],
                                          int(status.progress() * 100)))
    fh.seek(0)

    image = Image.open(fh)
    imageName = 'tmp/' + slugify(file['name']) + '.' + file['mimeType'].split('/')[1]
    open(imageName, 'a').close() # touch the file
    image.save(imageName)

    return imageName


def post_media_file(filename, data):
    """Takes a filename and media data dictionary."""
    image = Image.open(filename)
    for key in data.keys():
        data['medium[{}]'.format(key)] = data.pop(key)
    files = {
        'medium[attachment]': open(filename, 'rb')
    }
    response = requests.post(constants.API_MEDIA_ENDPOINT,
                             files=files,
                             data=data)
    response.raise_for_status()









