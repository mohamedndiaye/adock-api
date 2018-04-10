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
     working_area, completeness,
     numero_tva, created_at
    )
    select m.siret,
           m.raison_sociale,
           m.categorie_juridique,
           m.is_siege,
           s.numvoie || ' ' || s.typevoie || ' ' || s.libvoie as adresse,
           s.codpos,
           s.libcom,
          -- COALESCE(fs.telephone, '') as telephone,
          -- COALESCE(fs.email, '') as email,
           '', '',
           case s.dcret when '' then null else to_date(s.dcret, 'YYYYMMDD') end,
           case s.ddebact when '' then null else to_date(s.ddebact, 'YYYYMMDD') end,
           s.apen700,
           s.libapen,
           m.gestionnaire_de_transport,
           m.numero_lti,
           m.date_debut_validite_lti,
           m.date_fin_validite_lti,
           m.nombre_de_copies_lti_valides,
           m.numero_lc,
           m.date_debut_validite_lc,
           m.date_fin_validite_lc,
           m.nombre_de_copies_lc_valides,
           '', 40,
           'FR' || to_char((12 + 3 * (cast(s.siren::char(9) as bigint) % 97)) % 97, 'fm00') || s.siren,
           now()
    from marchandise as m
    inner join sirene as s
       on s.siret = m.siret;
-- TODO Update of addresses. Rewrite as UPSERT?
-- TODO Dashboard to display inconsistencies (if any)

commit;
