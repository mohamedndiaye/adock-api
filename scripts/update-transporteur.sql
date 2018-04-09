begin;

-- First query, try to find a corresonding SIRET in Sirène for each GRECO record.
with filtered_greco as (
    select s.siret, g.telephone, g.email
    from greco as g
    join sirene as s
      on g.siren = s.siren
    where g.localisation like '%' || s.numvoie || ' ' || s.typevoie || ' ' || s.libvoie || '%'
      and g.ville = s.libcom
)
-- Only applied if no validated data in transporteur
update transporteur t
   set email = coalesce(fg.email, ''),
       telephone = coalesce(fg.telephone, '')
  from filtered_greco fg
 where t.siret = fg.siret
   and t.validated_at is null;

with json_data as (
  select json_build_object('count', count(*), 'date', current_date) from transporteur
)
insert into meta (name, data)
    values (
        'transporteur',
        (select * from json_data)
    )
on conflict (name) do update
    set data = (select * from json_data);

commit;
