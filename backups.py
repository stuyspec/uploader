import ast

# TODO: get_email_by_name

def init():
    global users
    with open('wp-users-backup.txt', 'r') as f:
        users = ast.literal_eval(f.read())  # safer than eval()

def get_email_by_name(name):
    for uname, user_data in users.iteritems():
        print(name)
        if (name['firstname'] == user_data['firstname']
            and name['lastname'] == user_data['lastname']):
            print(user_data['email'])
            return user_data['email']
