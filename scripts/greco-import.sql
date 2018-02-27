-- The CSV file should be UTF-8 (tested with Unix format)
-- psql -d adock -v csv_file="greco.csv" -f greco-import.sql

\set csv_file 'greco.csv'

begin;

drop table if exists greco;
drop type if exists license_type;

create table greco (
    _register char,
    siren integer,
    name text,
    street text,
    zip_code int,
    city text,
    county_code int,
    phone text,
    email text,
    activity_start text,
    last_balance_sheet text,
    equity int,
    _import_finance text,
    _regime_derogatoire text,
    _motif_derogation text,
    license text,
    validity_end text,
    valid_copies int,
    invalid_copies int
);

create type license_type AS ENUM ('LCV', 'LCM', 'LTIM', 'LTIV', '');
\copy greco from 'greco.csv' with csv header delimiter '|' null '';
alter table greco
    drop _register,
    drop _import_finance,
    drop _regime_derogatoire,
    drop _motif_derogation,

    alter siren
     type char(9),

    alter license
     type license_type
    using replace(license, 'Pas de titre', '')::license_type,


commit;

-- Not unique SIREN
select siren, count(siren) from greco group by siren having count(siren) > 1;

-- Zip code inconsistency with county code
select siren, zip_code, county_code from greco where zip_code::char(2) != county_code::char(2);
