-- The CSV file should be UTF-8
-- The header contains an invalid character to delete before import.
-- psql -d adock -f greco-import.sql

begin;

drop table if exists greco;
drop type if exists licence_type;

create table greco (
    _registre char,
    siren integer,
    raison_sociale text,
    localisation text,
    code_postal varchar(5),
    ville text,
    _numero_departement int,
    telephone text,
    email text,
    inscription_activite text,
    date_dernier_bilan text,
    capitaux_propres int,
    _import_finance text,
    _regime_derogatoire text,
    _motif_derogation text,
    licence text,
    fin_validite text,
    copies_valides int,
    copies_non_valides int
);

create index greco_siren_idx on greco(siren);

create type licence_type AS ENUM ('LCV', 'LCM', 'LTIM', 'LTIV', '');

\copy greco from 'greco.csv' with csv header delimiter '|' null '';
alter table greco
    drop _registre,
    drop _import_finance,
    drop _regime_derogatoire,
    drop _motif_derogation,

    alter siren
     type char(9),

    alter licence
     type licence_type
    using replace(licence, 'Pas de titre', '')::licence_type,

    alter inscription_activite
     type date
    using to_date(inscription_activite, 'DD/MM/YYYY')::date,

    alter date_dernier_bilan
     type date
    using to_date(date_dernier_bilan, 'DD/MM/YYYY')::date,

    alter fin_validite
     type date
    using to_date(fin_validite, 'DD/MM/YYYY')::date
;
commit;

-- Not unique SIREN
with duplicated_siren as
(
    select siren, count(siren) from greco group by siren having count(siren) > 1
)
select count(*) from duplicated_siren;

-- Zip code inconsistency with county code
select siren, code_postal, _numero_departement
  from greco
 where code_postal::char(2) != _numero_departement::char(2);

-- Company not active anymore (closed) but still present in GRECO
select siren
  from greco
       left join sirene using(siren)
  where sirene.siren is null;

--- List of APET700 of companies in GRECO
-- select apet700
--   from greco
--   join sirene s using(siren)
--  group by s.apet700
--  order by s.apet700 asc;

--- Inconsistencies on zip code
-- select siren, g.code_postal, s.codpos
--   from greco g
--   join sirene s using(siren)
--  where g.code_postal != s.codpos;

--- More than one license type by siren
-- select siren, licence, count(licence)
--   from greco
-- group by siren, licence
-- having count(licence) > 1;
