-- The CSV file should be UTF-8
-- http://www2.transports.equipement.gouv.fr/registres/marchandises/SITR_Liste_des_entreprises_Marchandises_sortie_CSV.zip
-- If trailing empty line:
-- sed -i '$ d' Marchandises.txt

begin;

drop table if exists marchandise cascade;

create table marchandise (
    _situation text,
    _code_departement text,
    _nom_departement text,
    siret char(14),
    raison_sociale text,
    categorie_juridique text,
    code_postal varchar(5),
    commune text,
    is_siege char,
    gestionnaire_de_transport text,
    numero_lti varchar(16),
    date_debut_validite_lti text,
    date_fin_validite_lti text,
    nombre_de_copies_lti_valides text,
    numero_lc varchar(16),
    date_debut_validite_lc text,
    date_fin_validite_lc text,
    nombre_de_copies_lc_valides text
);

\copy marchandise from 'Marchandises.csv' with csv header delimiter as ',' null as '' quote '"';

alter table marchandise
    drop _situation,
    drop _code_departement,
    drop _nom_departement,

    alter is_siege
     type boolean
    using case is_siege when 'Y' then true else false end,

    alter date_debut_validite_lti
     type date
    using to_date(date_debut_validite_lti, 'DD/MM/YYYY')::date,

    alter date_fin_validite_lti
     type date
    using to_date(date_fin_validite_lti, 'DD/MM/YYYY')::date,

    alter date_debut_validite_lc
     type date
    using to_date(date_debut_validite_lc, 'DD/MM/YYYY')::date,

    alter date_fin_validite_lc
     type date
    using to_date(date_fin_validite_lc, 'DD/MM/YYYY')::date
;

create index marchandise_siret_idx on marchandise(siret);

commit;
