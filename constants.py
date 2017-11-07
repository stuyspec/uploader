SUBDOMAIN = 'not-deployed.yet'

API_ENDPOINT = 'http://{}'.format(SUBDOMAIN)
API_ARTICLES_ENDPOINT = 'http://{}/articles'.format(SUBDOMAIN)
API_AUTHORSHIPS_ENDPOINT = 'http://{}/authorships'.format(SUBDOMAIN)
API_SECTIONS_ENDPOINT = 'http://{}/sections'.format(SUBDOMAIN)
API_USERS_ENDPOINT = 'http://{}/users'.format(SUBDOMAIN)
API_ROLES_ENDPOINT = 'http://{}/roles'.format(SUBDOMAIN)
API_USER_ROLES_ENDPOINT = 'http://{}/user_roles'.format(SUBDOMAIN)
API_AUTH_ENDPOINT = 'http://{}/auth'.format(SUBDOMAIN)

def init(SUBDOMAIN):
    global API_ENDPOINT
    API_ENDPOINT = 'http://{}'.format(SUBDOMAIN)

    global API_ARTICLES_ENDPOINT
    API_ARTICLES_ENDPOINT = 'http://{}/articles'.format(SUBDOMAIN)

    global API_AUTHORSHIPS_ENDPOINT
    API_AUTHORSHIPS_ENDPOINT = 'http://{}/authorships'.format(SUBDOMAIN)

    global API_SECTIONS_ENDPOINT
    API_SECTIONS_ENDPOINT = 'http://{}/sections'.format(SUBDOMAIN)

    global API_USERS_ENDPOINT
    API_USERS_ENDPOINT = 'http://{}/users'.format(SUBDOMAIN)

    global API_ROLES_ENDPOINT
    API_ROLES_ENDPOINT = 'http://{}/roles'.format(SUBDOMAIN)

    global API_USER_ROLES_ENDPOINT
    API_USER_ROLES_ENDPOINT = 'http://{}/user_roles'.format(SUBDOMAIN)

    global API_AUTH_ENDPOINT
    API_AUTH_ENDPOINT = 'http://{}/auth'.format(SUBDOMAIN)