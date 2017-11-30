SUBDOMAIN = 'api.stuyspec.com'
API_ENDPOINT = 'http://{}'.format(SUBDOMAIN)
API_ARTICLES_ENDPOINT = 'http://{}/articles'.format(SUBDOMAIN)
API_AUTHORSHIPS_ENDPOINT = 'http://{}/authorships'.format(SUBDOMAIN)
API_MEDIA_ENDPOINT = 'http://{}/media'.format(SUBDOMAIN)
API_SECTIONS_ENDPOINT = 'http://{}/sections'.format(SUBDOMAIN)
API_USERS_ENDPOINT = 'http://{}/users'.format(SUBDOMAIN)
API_ROLES_ENDPOINT = 'http://{}/roles'.format(SUBDOMAIN)
API_USER_ROLES_ENDPOINT = 'http://{}/user_roles'.format(SUBDOMAIN)
API_OUTQUOTES_ENDPOINT = 'http://{}/outquotes'.format(SUBDOMAIN)
API_AUTH_ENDPOINT = 'http://{}/auth'.format(SUBDOMAIN)


def init(SUBDOMAIN=SUBDOMAIN):
    global API_ENDPOINT
    API_ENDPOINT = 'http://{}'.format(SUBDOMAIN)

    global API_ARTICLES_ENDPOINT
    API_ARTICLES_ENDPOINT = 'http://{}/articles'.format(SUBDOMAIN)

    global API_AUTHORSHIPS_ENDPOINT
    API_AUTHORSHIPS_ENDPOINT = 'http://{}/authorships'.format(SUBDOMAIN)

    global API_MEDIA_ENDPOINT
    API_MEDIA_ENDPOINT = 'http://{}/media'.format(SUBDOMAIN)

    global API_SECTIONS_ENDPOINT
    API_SECTIONS_ENDPOINT = 'http://{}/sections'.format(SUBDOMAIN)

    global API_USERS_ENDPOINT
    API_USERS_ENDPOINT = 'http://{}/users'.format(SUBDOMAIN)

    global API_ROLES_ENDPOINT
    API_ROLES_ENDPOINT = 'http://{}/roles'.format(SUBDOMAIN)

    global API_USER_ROLES_ENDPOINT
    API_USER_ROLES_ENDPOINT = 'http://{}/user_roles'.format(SUBDOMAIN)

    global API_OUTQUOTES_ENDPOINT
    API_OUTQUOTES_ENDPOINT = 'http://{}/outquotes'.format(SUBDOMAIN)

    global API_AUTH_ENDPOINT
    API_AUTH_ENDPOINT = 'http://{}/auth'.format(SUBDOMAIN)


SUPPORTED_MIME_TYPES = ['application/vnd.google-apps.audio', 'application/vnd.google-apps.document', 'application/vnd.google-apps.drawing', 'application/vnd.google-apps.file', 'application/vnd.google-apps.folder', 'application/vnd.google-apps.form', 'application/vnd.google-apps.fusiontable', 'application/vnd.google-apps.map', 'application/vnd.google-apps.photo', 'application/vnd.google-apps.presentation', 'application/vnd.google-apps.script', 'application/vnd.google-apps.sites', 'application/vnd.google-apps.spreadsheet', 'application/vnd.google-apps.unknown', 'application/vnd.google-apps.video', 'application/vnd.google-apps.drive-sdk']
