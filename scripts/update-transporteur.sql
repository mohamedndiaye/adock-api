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
     working_area, website, completeness,
     numero_tva, created_at, in_sirene)
    select m.siret,
           m.raison_sociale,
           m.categorie_juridique,
           m.is_siege,
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
           m.code_postal,
           m.commune,
           '', '',
           case s.dcret when '' then null else to_date(s.dcret, 'YYYYMMDD') end,
           case s.ddebact when '' then null else to_date(s.ddebact, 'YYYYMMDD') end,
           coalesce(s.apen700, ''),
           coalesce(s.libapen, ''),
           m.gestionnaire_de_transport,
           m.numero_lti,
           m.date_debut_validite_lti,
           m.date_fin_validite_lti,
           m.nombre_de_copies_lti_valides,
           m.numero_lc,
           m.date_debut_validite_lc,
           m.date_fin_validite_lc,
           m.nombre_de_copies_lc_valides,
           '', '', 40,
           'FR' || to_char((12 + 3 * (cast(m.siret::char(9) as bigint) % 97)) % 97, 'fm00') || m.siret::char(9),
           now(),
           -- In Sirene DB or not
           s.apen700 is not null
    from marchandise as m
    left join sirene as s
       on s.siret = m.siret
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
commit;

-- FIXME Delete transporteurs not marchandise

begin;
--- First query, try to find a corresonding SIRET in Sirène for each GRECO record.
with filtered_greco as (
    select s.siret, g.telephone, g.email
    from greco as g
    join sirene as s
      on g.siren = s.siren
    where g.localisation like '%' || s.numvoie || ' ' || s.typvoie || ' ' || s.libvoie || '%'
      and g.ville = s.libcom
)
--- Only applied if no validated data in transporteur.
--- It's possible to have several entries with the same SIRET so last one wins.
update transporteur t
   set email = coalesce(fg.email, ''),
       telephone = coalesce(fg.telephone, '')
  from filtered_greco fg
 where t.siret = fg.siret
   and t.validated_at is null;
commit;
