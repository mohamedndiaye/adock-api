begin;

insert into transporteur
    (siret, raison_sociale,
     categorie_juridique, is_siege,
     adresse, code_postal, ville,
     telephone, email,
     date_creation, debut_activite, code_ape, libelle_ape,
     gestionnaire,
     lti_numero, lti_date_debut, lti_date_fin, lti_nombre,
     lc_numero, lc_date_debut, lc_date_fin, lc_nombre,
     working_area, working_area_departements,
     website, completeness,
     numero_tva, created_at, in_sirene)
    select r.siret,
           r.raison_sociale,
           r.categorie_juridique,
           r.is_siege,
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
           r.code_postal,
           r.commune,
           '', '',
           case s.dcret when '' then null else to_date(s.dcret, 'YYYYMMDD') end,
           case s.ddebact when '' then null else to_date(s.ddebact, 'YYYYMMDD') end,
           coalesce(s.apen700, ''),
           coalesce(s.libapen, ''),
           r.gestionnaire_de_transport,
           r.numero_lti,
           r.date_debut_validite_lti,
           r.date_fin_validite_lti,
           r.nombre_de_copies_lti_valides,
           r.numero_lc,
           r.date_debut_validite_lc,
           r.date_fin_validite_lc,
           r.nombre_de_copies_lc_valides,
           '', array[s.depet],
           '', 40,
           case r.siret::char(1)
           when 'P'
            then ''
            else 'FR' || to_char((12 + 3 * (cast(r.siret::char(9) as bigint) % 97)) % 97, 'fm00') || r.siret::char(9)
           end,
           now(),
           -- In Sirene DB or not
           s.apen700 is not null
    from registre as r
    left join sirene as s
       on s.siret = r.siret
on conflict (siret) do
update set
  raison_sociale = excluded.raison_sociale,
  categorie_juridique = excluded.categorie_juridique,
  is_siege = excluded.is_siege,
  adresse = excluded.adresse,
  code_postal = excluded.code_postal,
  ville = excluded.ville,
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
  in_sirene = excluded.in_sirene;

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
