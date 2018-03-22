#!/bin/sh
coverage run --source='.' manage.py test adock
coverage html
