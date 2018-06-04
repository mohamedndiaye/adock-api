#!/bin/sh
../manage.py migrate &&
psql -d adock -f import-sirene.sql &&
../manage.py download_sirene &&
../manage.py update_sirene &&
psql -d adock -f import-greco.sql &&
../manage.py download_registre &&
../manage.py import_registre &&
psql -d adock -f update-transporteur.sql
