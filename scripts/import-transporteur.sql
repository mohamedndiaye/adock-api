begin;

-- The greco table doesn't contain the NIC so to find the corresponding
-- entry in the Sirène table, we add filtering on the address of the company.
-- It's not perfect because it's possible to have several institutions
-- to the same place but in our dataset only one company is in this situation.
--
-- To find inconsistencies:
--    select siret::char(9) as siren
--      from transporteur
--     group by siren
--       having count(*) > 1;
--
-- The greco table contains several rows with same SIREN because there is
-- one row by type of license for each company.
--
-- First query extracts the SIREN from greco and the corresponding NIC
-- found in Sirène table.
-- The second part adds the carrier to our table if it does exist already.
with filtered_siret as (
    select s.siren, s.nic, g.telephone, g.email, g.raison_sociale, g.localisation
    from greco as g
    join sirene as s
      on s.siren = g.siren and
         s.libcom = g.ville
    left join transporteur as t
      on t.siret = (s.siren || s.nic)
    where t.siret is null and
          g.localisation like '%' || s.numvoie || ' ' || s.typevoie || ' ' || s.libvoie || '%'
    group by s.siren, s.nic, g.telephone, g.email, g.raison_sociale, g.localisation
)
insert into transporteur
    (siret, raison_sociale, adresse, code_postal, ville,
     telephone, email,
     date_creation, debut_activite, code_ape, libelle_ape,
     lower_than_3_5_licenses, greater_than_3_5_licenses,
     numero_tva, created_at
    )
    select fs.siren || fs.nic as siret,
           fs.raison_sociale,
           fs.localisation as adresse,
           s.codpos, s.libcom,
           COALESCE(fs.telephone, '') as telephone,
           COALESCE(fs.email, '') as email,
           to_date(s.dcret, 'YYYYMMDD'),
           to_date(s.ddebact, 'YYYYMMDD'),
           s.apen700,
           s.libapen,
           0, 0,
           'FR' || to_char((12 + 3 * (cast(fs.siren::char(9) as bigint) % 97)) % 97, 'fm00') || fs.siren,
           now()
    from filtered_siret as fs
    inner join sirene as s
      on s.siren = fs.siren and s.nic = fs.nic
    left join transporteur as t
      on t.siret = (fs.siren || fs.nic)
    where t.siret is null
;
-- TODO Update of addresses. Rewrite as UPSERT?
-- TODO Dashboard to display inconsistencies (if any)

commit;
