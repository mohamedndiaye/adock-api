begin;

drop table if exists greco;

create table greco (
    id serial primary key,
    _registre char,
    siren text,
    raison_sociale text,
    localisation text,
    code_postal varchar(5),
    ville text,
    _numero_departement varchar(3),
    telephone text,
    email text,
    inscription_activite text,
    date_dernier_bilan text,
    capitaux_propres text,
    _import_finance text,
    _regime_derogatoire text,
    _motif_derogation text,
    licence text,
    fin_validite text,
    copies_valides int,
    copies_non_valides int
);

create index greco_siren_idx on greco(siren);

-- Don't know how to split this line :(
\copy greco (_registre, siren, raison_sociale, localisation, code_postal, ville, _numero_departement, telephone, email, inscription_activite, date_dernier_bilan, capitaux_propres, _import_finance, _regime_derogatoire, _motif_derogation, licence, fin_validite, copies_valides, copies_non_valides) from 'csv/greco.csv' with csv header null as '';

alter table greco
    drop _registre,
    drop _import_finance,
    drop _regime_derogatoire,
    drop _motif_derogation,

    alter inscription_activite
     type date
    using to_date(inscription_activite, 'DD/MM/YYYY')::date,

    alter date_dernier_bilan
     type date
    using to_date(date_dernier_bilan, 'DD/MM/YYYY')::date,

    alter fin_validite
     type date
    using to_date(fin_validite, 'DD/MM/YYYY')::date,

    add carrier_id varchar(14) default null;

-- Find a carrier to assign based on greco SIREN
update greco g
    set carrier_id = (select c.siret from carrier c where c.siret like concat(g.siren, '%') limit 1);

commit;
