#!/bin/sh
./manage.py sqlflush | psql -d adock && ./manage.py migrate && psql -d adock -f import-transporteur.sql
