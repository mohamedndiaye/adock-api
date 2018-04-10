#!/bin/sh
../manage.py migrate && psql -d adock -f import-all.sql
