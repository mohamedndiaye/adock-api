#!/bin/sh
# Take care to download the stock file of Sirene (https://www.data.gouv.fr/fr/datasets/base-sirene-des-entreprises-et-de-leurs-etablissements-siren-siret/)
# and to have the CSV files of GRECO
../manage.py migrate &&
psql -d adock -f import-sirene.sql &&
../manage.py download_sirene &&
../manage.py update_sirene &&
psql -d adock -f import-greco.sql &&
../manage.py download_registre &&
../manage.py import_registre &&
psql -d adock -f update-transporteur.sql &&
psql  -d adock -f update-transporteur-from-greco.sql &&
wget http://www.objectifco2.fr/docs/upload/107/2017-12-20%20Entreprises%20labellisees%20Objectif%20CO2.xlsx -O ../datafiles/objectif-co2-labellisees.xlsx &&
../manage.py import_objectif_co2 ../datafiles/objectif-co2-labellisees.xlsx
