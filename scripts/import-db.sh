#!/bin/sh
../manage.py migrate && psql adock -f sirene-import.sql && psql adock -f greco-import.sql
