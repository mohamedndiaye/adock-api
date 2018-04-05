Scripts d'import SQL
====================

Sources
-------

L'import de la base de données s'effectue à partir des données de la [liste des
entreprises](http://www2.transports.equipement.gouv.fr/registres/marchandises/SITR_Liste_des_entreprises_Marchandises_sortie_CSV.zip)
inscrites au registre des transports français.

Ces données sont complétées à l'insertion dans la base de données du projet A
Dock par celles issues du projet [Sirène](https://www.data.gouv.fr/fr/datasets/base-sirene-des-entreprises-et-de-leurs-etablissements-siren-siret/).

Seules les informations de téléphone et adresse électronique sont extraites dans
un second temps (mise à jour SQL) depuis la base de données GRECO.

Rôle des scripts
----------------

- `import-all.sh` créé la base de données, l'ensemble des tables et effectue
  tous les imports en s'appuyant sur `import-all.sql`

- `import-greco.sql` importe le fichier `greco.csv` contenant tous les exports
  CSV de la base de données GRECO dans une table spécifique pour l'extraction des
  téléphones et les adresses électroniques que contient cette base (avec un bémol
  sur la qualité de la source).

- `import-sirene.sql` importe les 11 millions d'enregistrements de la base
  Sirène (toutes les entreprises françaises), la table est uniquement utile pour
  compléter les informations sur les transporteurs au moment de l'import. Les informations
  de raison sociale, code APE, adresse, etc sont issues de cette base.

- `import-marchandise.sql` importe les entreprises inscrites au registre du commerce
  dans une table spécifique. Les informations sur les licences (LC, LTI), numéro,
  dates de validité, nombre ainsi que le gestionnaire sont issues de cette table.

- `import-transporteur.sh` est un script qui supprime toutes les tables de
  l'application Django (`reset-transporteur.sql`) et qui peuple la table
  `transporteur` à partir des autres tables (utilise `import-transporteur.sql`)

- `reset-transporteur.sql` permet de supprimer les tables Django de
  l'application ainsi que les tables métiers de l'application (par ex.
  `transporteur` et `transporteur_log`)

- `import-transporteur.sql` crée la table socle de l'application A Dock, elle
  est l'agrégation des tables `marchandise` et `sirene` et permet aux
  utilisateurs d'y ajouter des informations complémentaires (téléphone, adresse
  électronique, aire de travail, départements couverts, etc)

- `update-transporteur.sql` met à jour la table transporteur avec les numéros de
  téléphone et les adresses électroniques issues de GRECO uniquement s'ils
  n'ont pas été renseignés sur A Dock par l'utilisateur


