#!/bin/sh
# Take care to download the stock file of Sirene (https://www.data.gouv.fr/fr/datasets/base-sirene-des-entreprises-et-de-leurs-etablissements-siren-siret/)
# and to have the CSV files of GRECO
../manage.py migrate &&
../manage.py import_sirene_naf ../datafiles/int_courts_naf_rev_2.xlsx
psql -d adock -f import-sirene.sql &&
../manage.py download_sirene &&
../manage.py update_sirene &&
#psql -d adock -f import-greco.sql &&
../manage.py download_registre &&
../manage.py import_registre &&
psql -d adock -f update-carrier.sql &&
#psql  -d adock -f update-carrier-from-greco.sql &&
wget http://www.objectifco2.fr/docs/upload/107/2019-04-03%20Entreprises%20labellisees%20Objectif%20CO2.xlsx -O ../datafiles/objectif-co2-labellisees.xlsx &&
../manage.py import_objectif_co2 ../datafiles/objectif-co2-labellisees.xlsx
