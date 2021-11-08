# Action Network <-> NextCloud Integration

A small flask application to create [NextCloud](https://nextcloud.com/) users on request based on presence (and properties) of users in [Action Network](https://actionnetwork.org/). 

## Motivation & design

Created for Stroud District Green Party (where we use NextCloud for local file sharing), so that anyone who is currently a member of the Green Party of England and Wales (which uses Action Network to maintain membership information) and is linked to the local party, can get a NextCloud account. 

In order not to publicly reveal whether or not someone is a party member, the application will only send information to the e-mail address entered. Messages on screen do not reveal whether or not an e-mail address was found amongst registered users.

It's unlikely anyone else will have the exact same use case - but shared under MIT license just in case. 

## Configuration

Edit the `an_status_check` function in `app.py` to configure the action network variables checked for each potential nextcloud user. 

Copy `template.env` to `.env` and complete the following variables:

`NC_HOST=` - Nextcloud base URL

`NC_USER=` - Username of NextCloud user with API access

`NC_PASSWORD=` - Application password used for API access to NextCloud

`AN_KEY=` - ActionNetwork API Key

`MAIL_SERVER=` - SMTP server used to send e-amil

`MAIL_PORT=` - SMTP port used to send e-mail

`MAIL_USE_TLS=` - True or False for mail TLS use

`MAIL_USE_SSL=` - True or False for mail SSL use

`MAIL_USERNAME=` - Username for SMTP account

`MAIL_DISPLAYNAME=` - Name to be displayed in e-mail from line

`MAIL_PASSWORD=` - SMTP password

`RECAPTCHA_SITE_KEY=` - ReCaptcha **v2** credentials from https://www.google.com/recaptcha/admin/create

`RECAPTCHA_SECRET_KEY=` - As above

`NC_INSTANCE_NAME=` - What is the NextCloud instance known as (e.g. Local Campaign File Sharing Space)## Running

`AN_INSTANCE_NAME=` - What is the ActionNetwork instance known as (e.g. Green Party)

## Running

### Python

`gunicorn -w 4 app:app`

### Docker

`docker-compose up`

