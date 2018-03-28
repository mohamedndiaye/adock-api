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
    using case date_debut_validite_lti when '' then null else to_date(date_debut_validite_lti, 'DD/MM/YY')::date end,

    alter date_fin_validite_lti
     type date
    using case date_fin_validite_lti when '' then null else to_date(date_fin_validite_lti, 'DD/MM/YY')::date end,

    alter date_debut_validite_lc
     type date
    using case date_debut_validite_lc when '' then null else to_date(date_debut_validite_lc, 'DD/MM/YY')::date end,

    alter date_fin_validite_lc
     type date
    using case date_fin_validite_lc when '' then null else to_date(date_fin_validite_lc, 'DD/MM/YY')::date end,

    alter nombre_de_copies_lti_valides
     type integer
    using cast(nombre_de_copies_lti_valides as integer),

    alter nombre_de_copies_lc_valides
     type integer
    using cast(nombre_de_copies_lc_valides as integer)
;

create index marchandise_siret_idx on marchandise(siret);

commit;
