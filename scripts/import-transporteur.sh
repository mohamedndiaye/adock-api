#!/bin/sh
psql -d adock -f reset-transporteur.sql
../manage.py migrate && psql -d adock -f import-transporteur.sql
