# social-bootleg-api
This is a repository for our university team IT project
Project was made using Python 3.10, Flask and few Instagram scrapping libraries - instaloader, instascrape and instgramy (currently not in use)
For security reasons, login configuration was not pushed to git repository - PM me for JSON file

## Prerequisites
- python 3.10
- pip 21.2
- pipenv 2022.1.8

Check out this sample files and use them to create your own
- loginConfiguration.sample.json
- /social-bootleg/session_token.sample.json

## Build

### Install dependencies
```
pipenv install
```

### Create and activate a virtual environment
```
pipenv install
py -3 -m venv .venv
.venv\scripts\activate
```

### Start server (127.0.0.1:5000)
```
.\bootstrap
```