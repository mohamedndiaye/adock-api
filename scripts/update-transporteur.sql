begin;

insert into transporteur
    (siret,
     raison_sociale,
     enseigne,
     enseigne_unaccent,
     categorie_juridique,
     is_siege,
     adresse,
     code_postal, ville,
     departement,
     telephone, email,
     date_creation, debut_activite, code_ape, libelle_ape,
     gestionnaire,
     lti_numero, lti_date_debut, lti_date_fin, lti_nombre,
     lc_numero, lc_date_debut, lc_date_fin, lc_nombre,
     working_area,
     working_area_departements,
     website, completeness, description,
     numero_tva,
     created_at,
     deleted_at,
     sirene_deleted_at,
     objectif_co2)
    select r.siret,
           r.raison_sociale,
           coalesce(nullif(s.enseigne, ''), r.raison_sociale) as enseigne,
           unaccent(coalesce(nullif(s.enseigne, ''), r.raison_sociale)) as enseigne_unaccent,
           r.categorie_juridique,
           coalesce(s.siege = '1', r.is_siege) as is_siege,
           coalesce(
            s.numvoie ||
            case s.indrep
              when 'B' then ' bis'
              when 'T' then ' ter'
              when 'Q' then ' quater'
              when 'C' then ' quinquies'
              else ''
            end || ' ' || s.typvoie || ' ' || s.libvoie,
            '') as adresse,
           coalesce(s.codpos, r.code_postal) as code_postal,
           coalesce(s.libcom, r.commune) as ville,
           -- Departement is used for ranking
           r.code_departement as departement,
           '' as telephone, '' as email,
           case s.dcret when '' then null else to_date(s.dcret, 'YYYYMMDD') end as date_creation,
           case s.ddebact when '' then null else to_date(s.ddebact, 'YYYYMMDD') end as debut_activite,
           coalesce(s.apen700, '') as code_ape,
           coalesce(s.libapen, '') as libelle_ape,
           r.gestionnaire_de_transport as gestionnaire,
           r.numero_lti as lti_numero,
           r.date_debut_validite_lti as lti_date_debut,
           r.date_fin_validite_lti as lti_date_fin,
           r.nombre_de_copies_lti_valides as lti_nombre,
           r.numero_lc as lc_numero,
           r.date_debut_validite_lc as lc_date_debut,
           r.date_fin_validite_lc as lc_date_fin,
           r.nombre_de_copies_lc_valides as lc_nombre,
           'DEPARTEMENT' as working_area,
           -- Default departement for working area departements in company departement
           case when r.code_departement is null then null else array[r.code_departement] end as working_area_departements,
           '' as website, 40 as completeness, '' as description,
           case r.siret::char(1)
           when 'P'
            then ''
            else 'FR' || to_char((12 + 3 * (cast(r.siret::char(9) as bigint) % 97)) % 97, 'fm00') || r.siret::char(9)
           end as numero_tva,
           now() as created_at,
           -- Deleted from registre
           null as deleted_at,
           -- Deleted from Sirene
           case when s.apen700 is not null then null else now() end as sirene_deleted_at,
           '' as objectif_co2
    from registre as r
    left join sirene as s
       on s.siret = r.siret
on conflict (siret) do update
set
  raison_sociale = excluded.raison_sociale,
  enseigne = excluded.enseigne,
  categorie_juridique = excluded.categorie_juridique,
  is_siege = excluded.is_siege,
  adresse = excluded.adresse,
  code_postal = excluded.code_postal,
  ville = excluded.ville,
  departement = excluded.departement,
  date_creation = excluded.date_creation,
  debut_activite = excluded.debut_activite,
  code_ape = excluded.code_ape,
  libelle_ape = excluded.libelle_ape,
  gestionnaire = excluded.gestionnaire,
  lti_numero = excluded.lti_numero,
  lti_date_debut = excluded.lti_date_debut,
  lti_date_fin = excluded.lti_date_fin,
  lti_nombre = excluded.lti_nombre,
  lc_numero = excluded.lc_numero,
  lc_date_debut = excluded.lc_date_debut,
  lc_date_fin = excluded.lc_date_fin,
  lc_nombre = excluded.lc_nombre,
  deleted_at = null,
  sirene_deleted_at =
    case when excluded.sirene_deleted_at is null
     then null
     -- Keep the existing date if any
     else coalesce(transporteur.sirene_deleted_at, excluded.sirene_deleted_at)
    end;

--- Delete by setting the deleted_at attribute with current date (if not alreay deleted).
update transporteur
   set deleted_at = now()
 where not exists (select 1 from registre r where r.siret = transporteur.siret)
   and deleted_at is null;

-- Update meta stats
with json_data as (
  select json_build_object('count', count(*), 'date', current_date) from transporteur where deleted_at is null
)
insert into meta (name, data)
    values (
        'transporteur',
        (select * from json_data)
    )
on conflict (name) do update
    set data = (select * from json_data);

commit;
