import ast

# TODO: get_email_by_name

def init():
    global users
    with open('wp-users-backup.txt', 'r') as f:
        users = ast.literal_eval(f.read())  # safer than eval()

def get_email_by_name(name_dict):
    for uname, user_data in users.iteritems():
        if (name_dict['first_name'] == user_data['firstname']
            and name_dict['last_name'] == user_data['lastname']):
            return user_data['email']
    return ""
