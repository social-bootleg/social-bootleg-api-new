#!/bin/sh
export FLASK_APP=./social-bootleg/hello.py
source $(pipenv --venv)/bin/activate
flask run -h 0.0.0.0 --reload