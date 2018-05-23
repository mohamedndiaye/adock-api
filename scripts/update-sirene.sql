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
commit;
