-- Download the Sirene CSV from
-- Official: https://www.data.gouv.fr/fr/datasets/base-sirene-des-entreprises-et-de-leurs-etablissements-siren-siret/
-- Specs
-- https://static.data.gouv.fr/resources/base-sirene-des-entreprises-et-de-leurs-etablissements-siren-siret-page-en-cours-de-construction/20181001-193247/description-fichier-stocketablissement.pdf
-- cquest directory: http://data.cquest.org/geo_sirene/v2019/last/
-- cquest stock Active and closed: http://data.cquest.org/geo_sirene/v2019/last/StockEtablissement_utf8_geo.csv.gz
--
-- It requires around 2 minutes to import the DB...
begin;

drop table if exists sirene;
drop table if exists sirene_type_voie;

-- Fields copied into carrier table are marked with the letter 'U' for 'Used'

-- Liste des types de voies normalisées :

create table sirene_type_voie (
  code varchar(4),
  label varchar(32)
);

insert into sirene_type_voie (code, label)
values
  ('ALL', 'Allée'),
  ('AV', 'Avenue'),
  ('BD', 'Boulevard'),
  ('CAR', 'Carrefour'),
  ('CHE', 'Chemin'),
  ('CHS', 'Chaussée'),
  ('CITE', 'Cité'),
  ('COR', 'Corniche'),
  ('CRS', 'Cours'),
  ('DOM', 'Domaine'),
  ('DSC', 'Descente'),
  ('ECA', 'Écart'),
  ('ESP', 'Esplanade'),
  ('FG', 'Faubourg'),
  ('GR', 'Grande Rue'),
  ('HAM', 'Hameau'),
  ('HLE', 'Halle'),
  ('IMP', 'Impasse'),
  ('LD', 'Lieu dit'),
  ('LOT', 'Lotissement'),
  ('MAR', 'Marché'),
  ('MTE', 'Montée'),
  ('PAS', 'Passage'),
  ('PL', 'Place'),
  ('PLN', 'Plaine'),
  ('PLT', 'Plateau'),
  ('PRO', 'Promenade'),
  ('PRV', 'Parvis'),
  ('QUA', 'Quartier'),
  ('QUAI', 'Quai'),
  ('RES', 'Résidence'),
  ('RLE', 'Ruelle'),
  ('ROC', 'Rocade'),
  ('RPT', 'Rond Point'),
  ('RTE', 'Route'),
  ('RUE', 'Rue'),
  ('SEN', 'Sente-Sentier'),
  ('SQ', 'Square'),
  ('TPL', 'Terre-plein'),
  ('TRA', 'Traverse'),
  ('VLA', 'Villa'),
  ('VLGE', 'Village'),
  (' ', '');

create table sirene (
  siren varchar(9), -- U
  nic varchar(5), --- U
  siret varchar(14),
  statutDiffusionEtablissement varchar(1), -- U
  dateCreationEtablissement varchar(10), -- AAAA-MM-JJ
  trancheEffectifsEtablissement varchar(2), -- Code tranche
  anneeEffectifsEtablissement varchar(4), -- AAAA
  activitePrincipaleRegistreMetiersEtablissement varchar(6), -- NAFA
  dateDernierTraitementEtablissement timestamp, -- AAAA-MM-JJ
  etablissementSiege boolean,
  nombrePeriodesEtablissement int,
  -- Bad specs :( 38 -> 100
  complementAdresseEtablissement varchar(100),
  -- Bad data 4 -6
  numeroVoieEtablissement varchar(6),
  -- Bad data 1 -> 8
  indiceRepetitionEtablissement varchar(8),
  typeVoieEtablissement varchar(4),
  libelleVoieEtablissement varchar(100),
  codePostalEtablissement varchar(5),
  libelleCommuneEtablissement varchar(100),
  libelleCommuneEtrangerEtablissement varchar(100), -- Falllback if previous is empty
  -- Bad specs again 26 -> 64
  distributionSpecialeEtablissement varchar(64), -- Examples provided in specs
  codeCommuneEtablissement varchar(5),
  codeCedexEtablissement varchar(9),
  libelleCedexEtablissement varchar(100), -- If CEDEX
  codePaysEtrangerEtablissement varchar(5),
  libellePaysEtrangerEtablissement varchar(100),
  -- Wrong spec :( 38 -> 100
  complementAdresse2Etablissement varchar(100),
  -- Bad data 4 -> 6
  numeroVoie2Etablissement varchar(6),
  -- Bad data 1 -> 8
  indiceRepetition2Etablissement varchar(8),
  typeVoie2Etablissement varchar(4),
  libelleVoie2Etablissement varchar(100),
  codePostal2Etablissement varchar(5),
  libelleCommune2Etablissement varchar(100),
  libelleCommuneEtranger2Etablissement varchar(100),
  -- Bad specs again 26 -> 64
  distributionSpeciale2Etablissement varchar(64),
  codeCommune2Etablissement varchar(5),
  codeCedex2Etablissement varchar(9),
  libelleCedex2Etablissement varchar(100),
  codePaysEtranger2Etablissement varchar(5),
  libellePaysEtranger2Etablissement varchar(100),
  dateDebut varchar(10), -- AAAA-MM-JJ
  etatAdministratifEtablissement varchar(1), -- A : Actif, F : Fermé
  enseigne1Etablissement varchar(50),
  enseigne2Etablissement varchar(50),
  enseigne3Etablissement varchar(50),
  -- Bad specs 100 ->
  denominationUsuelleEtablissement varchar(200),
  activitePrincipaleEtablissement varchar(6), -- APE
  nomenclatureActivitePrincipaleEtablissement varchar(8),
  caractereEmployeurEtablissement varchar(1), -- O/N and could be null
  longitude float,
  latitude float,
  geo_score float,
  geo_type varchar(32),
  geo_adresse text,
  geo_id varchar(64),
  geo_ligne text,
  geo_l4 text,
  geo_l5 text
);

\copy sirene from '../datafiles/StockEtablissement_utf8_geo.csv' with csv header delimiter ',' null '' encoding 'utf-8';

alter table sirene add is_hidden boolean default false;
alter table sirene add is_deleted boolean default false;

create unique index sirene_siret_idx on sirene (siret);

commit;
