begin;

insert into carrier
    (siret,
     raison_sociale,
     enseigne,
     enseigne_unaccent,
     categorie_juridique,
     is_siege,
     adresse,
     code_postal, ville,
     departement,
     -- Was used to import GRECO information but not published (will be removed)
     telephone, email,
     date_creation, debut_activite, code_ape, libelle_ape,
     gestionnaire,
     lti_numero, lti_date_debut, lti_date_fin, lti_nombre,
     lc_numero, lc_date_debut, lc_date_fin, lc_nombre,
     completeness,
     numero_tva,
     created_at,
     deleted_at,
     sirene_exists,
     sirene_closed_at,
     objectif_co2,
     longitude,
     latitude)
    select r.siret,
           r.raison_sociale,
           coalesce(nullif(s.enseigne1Etablissement, ''), r.raison_sociale) as enseigne,
           unaccent(translate(coalesce(nullif(s.enseigne1Etablissement, ''), r.raison_sociale), ',.', '')) as enseigne_unaccent,
           r.categorie_juridique,
           coalesce(s.etablissementSiege = '1', r.is_siege) as is_siege,
           coalesce(s.numeroVoieEtablissement, '')
            || case s.indiceRepetitionEtablissement
                when 'B' then ' bis'
                when 'T' then ' ter'
                when 'Q' then ' quater'
                when 'C' then ' quinquies'
                else ''
              end
            || ' '
            || coalesce(stv.label, s.typeVoieEtablissement, '')
            || ' '
            || coalesce(s.libelleVoieEtablissement, '') as adresse,
           coalesce(s.codePostalEtablissement, r.code_postal) as code_postal,
           coalesce(s.libelleCommuneEtablissement, r.commune) as ville,
           -- Departement is used for ranking
           r.code_departement as departement,
           '' as telephone, '' as email,
           case s.dateCreationEtablissement when '' then null else to_date(s.dateCreationEtablissement, 'YYYY-MM-DD') end as date_creation,
           case s.dateDebut when '' then null else to_date(s.dateDebut, 'YYYY-MM-DD') end as debut_activite,
           coalesce(s.activitePrincipaleEtablissement, '') as code_ape,
           coalesce(sn.label, '') as libelle_ape,
           r.gestionnaire_de_transport as gestionnaire,
           r.numero_lti as lti_numero,
           r.date_debut_validite_lti as lti_date_debut,
           r.date_fin_validite_lti as lti_date_fin,
           r.nombre_de_copies_lti_valides as lti_nombre,
           r.numero_lc as lc_numero,
           r.date_debut_validite_lc as lc_date_debut,
           r.date_fin_validite_lc as lc_date_fin,
           r.nombre_de_copies_lc_valides as lc_nombre,
           40 as completeness,
           case r.siret::char(1)
           when 'P'
            then ''
            else 'FR' || to_char((12 + 3 * (cast(r.siret::char(9) as bigint) % 97)) % 97, 'fm00') || r.siret::char(9)
           end as numero_tva,
           now() as created_at,
           -- Deleted from registre
           null as deleted_at,
           -- Present in Sirene
           s.siret is not null as sirene_exists,
           -- Closed in Sirene
           case when s.etatAdministratifEtablissement = 'F' then s.dateDernierTraitementEtablissement else null end as sirene_closed_at,
           '' as objectif_co2,
           s.longitude,
           s.latitude
    from registre as r
    left join sirene as s
      on s.siret = r.siret
    left join sirene_type_voie stv
      on stv.code = s.typeVoieEtablissement
    -- Sirene DB contains invalid codes...
    left join sirene_naf sn
      on sn.code = s.activitePrincipaleEtablissement
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
  sirene_exists = excluded.sirene_exists,
  sirene_closed_at = excluded.sirene_closed_at,
  longitude = excluded.longitude,
  latitude = excluded.latitude;

--- Delete by setting the deleted_at attribute with current date (if not alreay deleted).
update carrier
   set deleted_at = now()
 where not exists (select 1 from registre r where r.siret = carrier.siret)
   and deleted_at is null;

-- Create default carrier editable (really nice query BTW :)
with new_carrier_editable AS (
  insert into carrier_editable (
      carrier_id,
      telephone,
      email,
      created_at,
      confirmed_at,
      working_area,
      working_area_departements,
      specialities,
      website,
      description
    )
    select
      siret,
      '' as telephone,
      '' as email,
      now() as created_at,
      null as confirmed_at,
      'DEPARTEMENT' as working_area,
      -- Default departement for working area departements in company departement
      case when departement is null then null else array[departement] end as working_area_departements,
      null as specialities,
      '' as website,
      '' as description
    from carrier
    where carrier.editable_id is null
  returning *
) update carrier set editable_id = nce.id from new_carrier_editable nce where siret = nce.carrier_id;

-- Update meta stats
with json_data as (
  select json_build_object('count', count(*), 'date', current_date) from carrier where deleted_at is null and sirene_closed_at is null
)
insert into meta (name, data)
    values (
        'carrier',
        (select * from json_data)
    )
on conflict (name) do update
    set data = (select * from json_data);

commit;
