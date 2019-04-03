--- The GRECO database has been manually extracted as CSV files to bootstrap the project.
--- There is no intent to update it again so the script has been separated from the daily
--- update management.
 --- First query, try to find a corresonding SIRET in Sirene for each GRECO record.
with filtered_greco as
  (select s.siret,
          g.telephone,
          g.email
   from greco as g
   join sirene as s on g.siren = s.siren
   where g.localisation like '%' || s.numvoie || ' ' || s.typvoie || ' ' || s.libvoie || '%'
     and g.ville = s.libcom ) --- Only applied if no validated data in carrier.
--- It's possible to have several entries with the same SIRET so last one wins.
 
update carrier c
set email = coalesce(fg.email, ''), 
    telephone = coalesce(fg.telephone, '')
from carrier_editable ce,
     filtered_greco fg
where c.siret = fg.siret
  and c.editable_id = ce.id
  and ce.confirmed_at is null;
