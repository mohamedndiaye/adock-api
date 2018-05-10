begin;

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
