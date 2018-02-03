# Troubleshooting

- [('Connection aborted.', error("(32, 'EPIPE')",))](#connection-aborted-error32-epipe)
- [422 Client Error: Unprocessable Entity for url: .../auth]

### ('Connection aborted.', error("(32, 'EPIPE')",))

S3 has a concept of virtual addressing and path style addressing. Virtual host style is preferred, but it relies on DNS propagation and so until that has happened, S3 sends a redirect when you make a request on the virtual host. The problem is the way the API handles different body types. For file-like objects, it will send a packet before the rest of the body. It will then have time to receive the redirect. For raw string or bytes, however, it will send everything in one go. If that results in a big enough body, S3 will close the connection.

To make sure this error comes from the file being too big, log into the AWS console and navigate to the Elastic Beanstalk service. Select the application API you tried to upload to and navigate to the logs. Request the last 100 lines.

The top part of the log should be the nginx error log. If the file was too big, the error log will look something like this:
```
-------------------------------------
/var/log/nginx/error.log
-------------------------------------
...
TIMESTAMP [error] 3059#0: *80895 client intended to send too large body: 13711059 bytes
...
```

You will need to reload the nginx configuration or change the client body maximum size.
```sh
# SSH using Elastic Beanstalk CLI

$ eb ssh
 _____ _           _   _      ____                       _        _ _
| ____| | __ _ ___| |_(_) ___| __ )  ___  __ _ _ __  ___| |_ __ _| | | __
|  _| | |/ _` / __| __| |/ __|  _ \ / _ \/ _` | '_ \/ __| __/ _` | | |/ /
| |___| | (_| \__ \ |_| | (__| |_) |  __/ (_| | | | \__ \ || (_| | |   <
|_____|_|\__,_|___/\__|_|\___|____/ \___|\__,_|_| |_|___/\__\__,_|_|_|\_\
                                       Amazon Linux AMI

This EC2 instance is managed by AWS Elastic Beanstalk. Changes made via SSH
WILL BE LOST if the instance is replaced by auto-scaling. For more information
on customizing your Elastic Beanstalk environment, see our documentation here:
http://docs.aws.amazon.com/elasticbeanstalk/latest/dg/customize-containers-ec2.html
[ec2-user@ip-172-31-84-126 ~]$ 
```

After ssh-ing into our EC2 instance, check to see if your nginx configuration has the correct maxiumum size: `20M` (20 megabytes).
```sh
# nano the proxy.conf

$ cd /etc/nginx/conf.d
$ cat proxy.conf
client_max_body_size 20M;
```

If proxy.conf does not exist or `cat`-ing it does not have the output, create it/modify it with `sudo nano proxy.conf`. Then, test the new config (`sudo nginx -t`).

Reload the nginx service (`sudo service nginx reload`).


### 422 Client Error: Unprocessable Entity for url: .../auth

This usually means that the uploader tried to make an account with an email that has already been taken. It is probable that the author/artist's name in the Google Doc or media input has a typo or is a nickname. Log into the AWS console and navigate to the Elastic Beanstalk service. Select the application API you tried to upload to and navigate to the logs. Request the last 100 lines and find the email that triggered the 422 error.

In the rails console (directions in the previous troubleshooting section) find the User with that email (`User.find_by(email: FAULTY_EMAIL)`). If the `first_name` and `last_name` of the user are correct, re-run the cli-uploader and enter the correct names when prompted. If the names in the database are incorrect, fix them in the rails console:

```rb
# Find the user with the taken email
> u = User.find_by(email: "FAULTY_EMAIL")

# Change the names
> u.first_name = CORRECT_FIRST_NAME
> u.last_name = CORRECT_LAST_NAME

# Update the user in the database
> u.save
```

After the names are fixed, re-run the cli-uploader.