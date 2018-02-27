-- The CSV file should be UTF-8
-- The header contains an invalid character to delete before import.
-- psql -d adock -f greco-import.sql

begin;

drop table if exists greco;
drop type if exists license_type;

create table greco (
    _register char,
    siren integer,
    name text,
    street text,
    zip_code varchar(5),
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

create index greco_siren_idx on greco(siren);

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

    alter activity_start
     type date
    using to_date(activity_start, 'DD/MM/YYYY')::date,

    alter last_balance_sheet
     type date
    using to_date(last_balance_sheet, 'DD/MM/YYYY')::date,

    alter validity_end
     type date
    using to_date(validity_end, 'DD/MM/YYYY')::date
;
commit;

-- Not unique SIREN
with duplicated_siren as
(
    select siren, count(siren) from greco group by siren having count(siren) > 1
)
select count(*) from duplicated_siren;

-- Zip code inconsistency with county code
select siren, zip_code, county_code from greco where zip_code::char(2) != county_code::char(2);

-- Company not active anymore (closed) but still present in GRECO
select siren
  from greco
       left join sirene using(siren)
  where sirene.siren is null;

-- Inconsistencies on zip code (code postal)
-- select siren, zip_code, codpos
--   from greco
--   join sirene using(siren)
--  where zip_code != codpos;
