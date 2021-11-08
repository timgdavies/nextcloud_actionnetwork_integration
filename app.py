# https://docs.nextcloud.com/server/latest/admin_manual/configuration_user/reset_user_password.html
import re
import requests
import secrets
import os
from flask import Flask, request, redirect, render_template, send_file
from flask_mail import Mail, Message
from flask_recaptcha import ReCaptcha
import urllib.parse


an_api_key = os.environ.get("AN_API_KEY") # Expects an Action Nework API Key
nc_host = os.environ.get("NC_HOST") # Expects the root URL of the NextCloud instance
nc_user = os.environ.get("NC_USER") # Expects a nextcloud username for an account with API access
nc_password = os.environ.get("NC_PASSWORD") # Expects an app password for the username above)
nc_url = nc_host.replace("://","://{}:{}@".format(nc_user, nc_password)) 
nc_instance_name = os.environ.get("NC_INSTANCE_NAME")
an_instance_name = os.environ.get("AN_INSTANCE_NAME")

app = Flask(__name__)

app.config['MAIL_SERVER'] = os.environ.get("MAIL_SERVER")
app.config['MAIL_PORT'] = os.environ.get("MAIL_PORT")
app.config['MAIL_USE_SSL'] = os.environ.get("MAIL_USE_SSL")
app.config['MAIL_USERNAME'] = os.environ.get("MAIL_USERNAME")
app.config['MAIL_DISPLAYNAME'] = os.environ.get("MAIL_DISPLAYNAME")
app.config['MAIL_PASSWORD'] = os.environ.get("MAIL_PASSWORD")
app.config['RECAPTCHA_ENABLED'] = True
app.config['RECAPTCHA_SITE_KEY'] = os.environ.get("RECAPTCHA_SITE_KEY")
app.config['RECAPTCHA_SECRET_KEY'] = os.environ.get("RECAPTCHA_SECRET_KEY")

recaptcha = ReCaptcha(app=app)
mail = Mail(app)


def an_status_check(person):
    "Action Network Status Check. This will need to be customised depending on the fields that should be checked in any given instance."
    if(person['custom_fields']['Membership_Status'] == 'Current' and person['custom_fields']['Local_Party'] == "Stroud District Green Party"):
        return True
    else:
        return False

@app.route("/")
def main():
    return render_template('form.html', nc_host=nc_host, email='', message='')


@app.route("/action", methods=['GET', 'POST'])
def check_user():
    email = request.form['email']

    if recaptcha.verify():
        nc_users = search_nc_user(email)

        if not nc_users['ocs']['meta']['status'] == 'ok':
            return render_template('error.html', nc_host=nc_host, nc_instance_name=nc_instance_name)
        if len(nc_users) > 1:
            return render_template('error.html', nc_host=nc_host, nc_instance_name=nc_instance_name)
        elif len(nc_users['ocs']['data']['users']) == 1:
            if reset_nc_password(nc_users['ocs']['data']['users'][0], email):
                return render_template('message.html', nc_host=nc_host, message="E-mail sent")
            else:
                return render_template('error.html', nc_host=nc_host, nc_instance_name=nc_instance_name)
        else:
            # We didn't find a nextcloud user, check them in ActionNetwork
            an_user = search_an_users(email)
            if an_user:
                create_nc_user(an_user, email)
            else:
                msg = Message("{} account information".format(nc_instance_name),
                sender=(app.config['MAIL_DISPLAYNAME'], app.config['MAIL_USERNAME']),
                recipients=[email],
                body=render_template('mail_no_account.txt', nc_instance_name=nc_instance_name, an_instance_name=an_instance_name, email=email))
                mail.send(msg)
        
        return render_template('message.html', nc_host=nc_host, message="E-mail sent")
    else:
        return render_template('form.html', nc_host=nc_host, email=email, message='CAPTCHA not completed correctly. Please try again.')


def search_nc_user(email):
    "Search for a NextCloud user by e-mail address"
    nc_headers = {'OCS-APIRequest': 'true'}
    ncr = requests.get(
        nc_url+"/ocs/v1.php/cloud/users?format=json&search={}".format(urllib.parse.quote(email)), headers=nc_headers)
    return ncr.json()

def create_nc_user(an_user, email):
    "Create a new nextcloud user based on an Action Network user"
    nc_headers = {'OCS-APIRequest': 'true'}
    password = secrets.token_urlsafe(15)
    username = re.sub(r'\W+', '', an_user['given_name']+an_user['family_name'])
    displayname = "{} {}".format(an_user['given_name'], an_user['family_name'])
    payload = {"userid": username,
               "password": password,
               "displayName": displayname,
               "email": email,
               "groups[]": ["Members"]
               }
    ncr = requests.post(nc_url+"/ocs/v1.php/cloud/users?format=json",
                        data=payload,
                        headers=nc_headers)
    print("Trying to create user")
    print(payload)
    print(ncr.json())
    if ncr.json()['ocs']['meta']['status'] == 'ok':
        msg = Message("Your {} account has been created".format(nc_instance_name),
                      sender=(app.config['MAIL_DISPLAYNAME'],
                              app.config['MAIL_USERNAME']),
                    recipients=[email],
                    body=render_template('mail_new_account.txt', nc_host=nc_host, displayname=displayname, username=username, email=email, password=password, nc_instance_name=nc_instance_name))
        mail.send(msg)
        return True
    else:
        return False
    
    pass
    
def reset_nc_password(user, email):
    "Create a new password for a NextCloud user and send it to them by e-mail"
    nc_headers = {'OCS-APIRequest': 'true'} 
    password = secrets.token_urlsafe(15)
    ncr = requests.put(nc_url+"/ocs/v1.php/cloud/users/{}?format=json".format(user),
                            data={"key":"password", "value": password},
                            headers=nc_headers)
    if ncr.json()['ocs']['meta']['status'] == "ok":
        msg=Message("Your {} account password has been reset".format(nc_instance_name),
                    sender=(app.config['MAIL_DISPLAYNAME'],
                            app.config['MAIL_USERNAME']),
                    recipients=[email],
                    body=render_template('mail_password_reset.txt', nc_host=nc_host, user=user, email=email, password=password, nc_instance=nc_instance_name))
        mail.send(msg)
        return True
    else:
        return False

def search_an_users(email):
    "Search for an Action Network user by e-mail address"
    an_headers = {'OSDI-API-Token': an_api_key }
    anr = requests.get("https://actionnetwork.org/api/v2/people?filter=email_address eq '{}'".format(email),
        headers=an_headers)
    try:
        if len(anr.json()['_embedded']['osdi:people']) == 1:
            if an_status_check(anr.json()['_embedded']['osdi:people'][0]):
                return anr.json()['_embedded']['osdi:people'][0]
            else:
                return False
        else:
            return False
    except:
        return False


if __name__ == '__main__':
	app.run(host="0.0.0.0", debug=True)
