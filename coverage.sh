#!/bin/sh
coverage run --source='.' manage.py test adock -k && coverage html
