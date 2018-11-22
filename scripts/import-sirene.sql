-- Download the Sirene CSV from
-- https://www.data.gouv.fr/fr/datasets/base-sirene-des-entreprises-et-de-leurs-etablissements-siren-siret/
-- It takes 6 minutes to import the full sirene DB on my laptop with SSD (+ 1 mn with index)
-- almost 11 millions of records.

begin;

drop table if exists sirene;

-- Fields copied into carrier table are marked with the letter 'U' for 'Used'
create table sirene (
    -- U
    siren char(9),
    -- U
    nic char(5),
    --- Adresse normalisée
    l1_normalisee varchar(38),
    l2_normalisee varchar(38),
    l3_normalisee varchar(38),
    l4_normalisee varchar(38),
    l5_normalisee varchar(38),
    l6_normalisee varchar(38),
    l7_normalisee varchar(38),

    --- Adresse déclarée
    l1_declaree varchar(38),
    l2_declaree varchar(38),
    l3_declaree varchar(38),
    l4_declaree varchar(38),
    l5_declaree varchar(38),
    l6_declaree varchar(38),
    l7_declaree varchar(38),

    -- U - Adresse géographique
    numvoie varchar(4),
    -- B (bis), T (ter), Q (quarter), etc
    indrep varchar(1),
    -- U
    typvoie varchar(4),
    -- U
    libvoie varchar(32),
    -- U
    codpos varchar(5),
    cedex varchar(5),

    --- Localisation géographique de l'établissement
    rpet varchar(2),
    libreg varchar(70),
    depet varchar(2),
    arronet varchar(2),
    ctonet varchar(3),
    comet varchar(3),
    -- U - Commune de l'établissement
    libcom varchar(32),
    du varchar(2),
    -- Taille de l'unité urbaine
    tu varchar(1),
    uu varchar(2),
    epci varchar(9),
    -- Tranche de commune détaillée
    tcd varchar(2),
    -- Zone d'emploi
    zemet varchar(4),

    --- Informations sur l'établissement
    -- Établissement siège 1 ou non siège 0
    siege varchar(1),
    -- ERREUR La documentation indique 40
    enseigne varchar(50),
    ind_publipo varchar(1),
    diffcom varchar(1),
    -- Année, mois introduction dans la base AAAAMM
    amintret varchar(6),

    --- Caractéristiques économiques de l'établissement
    -- Nature de l'établissement https://www.sirene.fr/sirene/public/variable/natetab
    natetab varchar(1),
    libnatetab varchar(30),
    apet700 varchar(5),
    libapet varchar(65),
    -- année de validité de l'activité principale de l'établissement AAAA
    dapet varchar(5),
    -- tranche effectif salarié de l'établissement
    tefet varchar(2),
    libtefet varchar(23),
    efetcent varchar(6),
    -- Année de validité de l'effectif salarié de l'établissement
    defet varchar(4),
    origine varchar(2),
    -- U - Date de création de l'établissement AAAAMMJJ
    dcret varchar(8),
    -- U - Date de début d'activité
    ddebact varchar(8),
    activnat varchar(2),
    lieuact varchar(2),
    actisurf varchar(2),
    saisonat varchar(2),
    modet varchar(1),
    prodet varchar(1),
    prodpart varchar(1),
    auxilt varchar(1),

    --- Identification de l'entreprise
    -- Nom ou raison sociale de l'entreprise
    nomen_long varchar(131),
    sigle varchar(30),
    -- Nom de naissance
    nom varchar(100),
    prenom varchar(30),
    -- 1 Monsieur, 2 Madame
    civilite varchar(1),
    rna varchar(10),

    --- Informations sur le siège de l'entreprise
    nicsiege varchar(5),
    -- région de localisation de l'entreprise
    -- https://www.sirene.fr/sirene/public/variable/rpen
    rpen varchar(2),
    -- Département et commune de localisation du siège de l'entreprise
    -- ERREUR signalée à sirene.fr sur la longueur du champ (2 -> 5)
    depcomen varchar(5),
    adr_mail varchar(80),

    --- Caractéristiques économiques de l'entreprise
    -- Nature juridique de l'entreprise
    nj varchar(4),
    libnj varchar(100),
    -- U - Code activité
    apen700 varchar(5),
    -- U - Libelle activité
    libapen varchar(65),
    -- AAAA
    dapen varchar(4),
    aprm varchar(6),
    ess varchar(1),
    dateess varchar(8),
    tefen varchar(2),
    libtefen varchar(23),
    efencent varchar(6),
    defen varchar(4),
    categorie varchar(5),
    dcren varchar(8),
    amintren varchar(6),
    monoact varchar(1),
    moden varchar(1),
    proden varchar(1),
    esaann varchar(4),
    tca varchar(1),
    esaapen varchar(5),
    esasec1n varchar(5),
    esasec2n varchar(5),
    esasec3n varchar(5),
    esasec4n varchar(5),

    --- Données spécifiques aux mises à jour
    vmaj varchar(1),
    vmaj1 varchar(1),
    vmaj2 varchar(1),
    vmaj3 varchar(1),
    -- AAAA-MM-JJTHH:MM:SS
    -- - AAAA est l'année,
    -- - MM le mois,
    -- - JJ le jour,
    -- - T (time) séparateur de la date par rapport à l'heure,
    -- - HH l'heure, MM les minutes et SS les secondes.
    datemaj varchar(19),
    longitude float,
    latitude float,
    geo_score float,
    geo_type varchar(32),
    geo_adresse text,
    geo_id varchar(32),
    geo_ligne text,
    geo_l4 text,
    geo_l5 text
);

\copy sirene from 'csv/geo-sirene.csv' with csv header delimiter ';' null '' encoding 'ISO-8859-1';

-- Slow but I'm not able to speed up the process by defining them in 'create table'
-- because I have issues to specify the columns to copy from the CSV file

alter table sirene add siret char(14);
alter table sirene add is_hidden boolean default false;
alter table sirene add is_deleted boolean default false;

alter table sirene
    alter siret
    type char(14)
    using siren || nic,

    alter siret
    set not null;

create index sirene_siren_idx on sirene(siren);
create unique index sirene_siret_idx on sirene(siret);

commit;
