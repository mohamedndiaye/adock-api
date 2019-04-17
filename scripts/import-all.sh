#!/bin/sh
../manage.py migrate &&
../manage.py import_sirene_naf ../datafiles/int_courts_naf_rev_2.xlsx
psql -d adock -f import-sirene.sql &&
../manage.py download_sirene &&
../manage.py import_sirene &&
../manage.py download_registre &&
../manage.py import_registre &&
psql -d adock -f update-carrier.sql &&
wget http://www.objectifco2.fr/docs/upload/107/2019-04-03%20Entreprises%20labellisees%20Objectif%20CO2.xlsx -O ../datafiles/objectif-co2-labellisees.xlsx &&
../manage.py import_objectif_co2 ../datafiles/objectif-co2-labellisees.xlsx
