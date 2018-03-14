begin;

-- The greco table doesn't contain the NIC so to find the corresponding
-- entry in the Sirène table, we add filtering on the address of the company.
-- It's not perfect because it's possible to have several institutions
-- to the same place but in our dataset only one company is in this situation.
--
-- To find inconsistencies:
--    select siret::char(9) as siren
--      from transporteurs_transporteur
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
    select s.siren, s.nic, g.telephone, g.email
    from greco as g
    join sirene as s
      on s.siren = g.siren and
         s.libcom = g.ville
    left join transporteurs_transporteur as t
      on t.siret = (s.siren || s.nic)
    where t.siret is null and
          g.localisation like '%' || s.numvoie || ' ' || s.typevoie || ' ' || s.libvoie || '%'
    group by s.siren, s.nic, g.telephone, g.email
)
insert into transporteurs_transporteur
    (siret, raison_sociale, adresse, code_postal, ville,
     telephone, email,
     date_creation, debut_activite, code_ape, libelle_ape,
     lower_than_3_5_licenses, greater_than_3_5_licenses, created_at)
    select fs.siren || fs.nic as siret,
           s.nomen_long,
           s.numvoie || ' ' || s.typevoie || ' ' || s.libvoie as adresse,
           s.codpos, s.libcom,
           COALESCE(fs.telephone, '') as telephone,
           COALESCE(fs.email, '') as email,
           to_date(s.dcret, 'YYYYMMDD'),
           to_date(s.ddebact, 'YYYYMMDD'),
           s.apen700,
           s.libapen,
           0, 0, now()
    from filtered_siret as fs
    inner join sirene as s
      on s.siren = fs.siren and s.nic = fs.nic
    left join transporteurs_transporteur as t
      on t.siret = (fs.siren || fs.nic)
    where t.siret is null
;
-- TODO Update of addresses. Rewrite as UPSERT?

-- Reset the values before the update
update transporteurs_transporteur
   set lower_than_3_5_licenses = 0,
       greater_than_3_5_licenses = 0;

-- Update the current number of licenses for merchandise (travelers are excluded)
-- Fast but a seq scan is used (create partial index?)
update transporteurs_transporteur as t
   set lower_than_3_5_licenses = case when g.licence = 'LCM'
                                      then g.copies_valides
                                      else lower_than_3_5_licenses
                                  end,
       greater_than_3_5_licenses = case when g.licence = 'LTIM'
                                        then g.copies_valides
                                        else greater_than_3_5_licenses
                                    end
  from greco as g
 where t.siret::char(9) = g.siren;

commit;
-- TODO Dashboard to display inconsistencies (if any)
