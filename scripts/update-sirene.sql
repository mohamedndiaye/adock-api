begin;

drop table if exists sirene_update;
create table sirene_update(like sirene);

alter table sirene_update drop siret;
alter table sirene_update drop is_deleted;
alter table sirene_update drop is_hidden;

alter table sirene_update add eve varchar(4);
alter table sirene_update add dateve varchar(8);
alter table sirene_update add typcreh varchar(1);
alter table sirene_update add dreactet varchar(8);
alter table sirene_update add dreacten varchar(8);
alter table sirene_update add madresse varchar(1);
alter table sirene_update add menseigne varchar(1);
alter table sirene_update add mapet varchar(1);
alter table sirene_update add mprodet varchar(1);
alter table sirene_update add mauxilt varchar(1);
alter table sirene_update add mnomen varchar(1);
alter table sirene_update add msigle varchar(1);
alter table sirene_update add mnicsiege varchar(1);
alter table sirene_update add mnj varchar(1);
alter table sirene_update add mapen varchar(1);
alter table sirene_update add mproden varchar(1);
alter table sirene_update add siretps varchar(14);
alter table sirene_update add tel varchar(14);

--- cat update-sirene.sql | sed s:FILENAMEPLACEHOLDER:foo.csv:g | psql adock
\copy sirene_update from 'FILENAMEPLACEHOLDER' with csv header delimiter ';' null '' encoding 'ISO-8859-1';

insert into sirene (
        siret,
        siren,
        nic,
        numvoie,
        indrep,
        typvoie,
        libvoie,
        codpos,
        libcom,
        dcret,
        ddebact,
        apen700,
        libapen,
        is_hidden
    )
    select siren || nic as siret,
        siren,
        nic,
        numvoie,
        indrep,
        typvoie,
        libvoie,
        codpos,
        libcom,
        dcret,
        ddebact,
        apen700,
        libapen,
        false
    from sirene_update su
    where vmaj in ('C', 'D')
      and not exists (
        select 1
        from sirene s
        where s.siren = su.siren
          and s.nic = su.nic
      );

-- 'I' Initial is ignored
-- Sort by datemaj
update sirene s
    set numvoie = su.numvoie,
        indrep = su.indrep,
        typvoie = su.typvoie,
        libvoie = su.libvoie,
        codpos = su.codpos,
        libcom = su.libcom,
        dcret = su.dcret,
        ddebact = su.ddebact,
        apen700 = su.apen700,
        libapen = su.libapen,
        is_hidden = (su.vmaj = 'O'),
        is_deleted = (su.vmaj = 'E')
    from (
        select *
        from sirene_update
        where vmaj in ('D', 'O', 'F', 'E')
        order by datemaj
        for update
    ) as su
    where su.siren = s.siren
      and su.nic = s.nic;

commit;
