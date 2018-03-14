#!/bin/sh
createdb adock && ../manage.py migrate && psql -d adock -f import-db.sql
