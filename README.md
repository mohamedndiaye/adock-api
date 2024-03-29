[![CircleCI](https://circleci.com/gh/MTES-MCT/adock-api.svg?style=svg)](https://circleci.com/gh/MTES-MCT/adock-api)

# A Dock

> Simplifions les relations transporteurs/chargeurs

## Description

Ce dépôt contient le code source de l'application serveur du projet A Dock. Le
serveur fournit une API REST sans authentification qui permet la consultation et
la modification des informations de contact de la base de données des
transporteurs.

L'application est écrite en [Python][python] avec le framework [Django][django]
et s'appuie sur une base de données [PostgreSQL][postgresql]. Cette application
utilise des extensions spécifiques à PostgreSQL (`jsonb`, champs de type
`array`, index de trigrammes, etc).

## Sources des données

L'import de la base de données s'effectue à partir des données de la [liste des
entreprises](http://www2.transports.equipement.gouv.fr/registres/marchandises/SITR_Liste_des_entreprises_Marchandises_sortie_CSV.zip)
inscrites au registre des transports français.

Ces données sont complétées à l'insertion dans la base de données du projet A
Dock par celles issues du projet [Sirene](https://www.data.gouv.fr/fr/datasets/base-sirene-des-entreprises-et-de-leurs-etablissements-siren-siret/).

Les données sont aussi complétées avec l'import des entreprises labellisées par
la charte [Objectif CO2](http://www.objectifco2.fr/index/documents#categ-6).

Les informations sont ensuite modifiées (champs téléphone et adresse
électronique) et étendues (aire de travail, départements, spécialités et site
Web) via l'application.

## Actualisation des données

Afin de mettre à jour les informations des entreprises des mises à jour sont
effectués chaque jour par un traitement automatisé. Ces traitements consistent à
collecter le flux quotidien de la base de données Sirene et à relire la base de
jour actuelle du registre des transports.

Seules les données non modifiables de la base de données A Dock sont mises à
jour.

## Description des scripts SQL et des commandes Django

Les scripts SQL portent l'extension `.sql` dans leur description à la différence
des commandes Django :

- `import-all.sh` créé la base de données initiale, l'ensemble des tables et
  effectue tous les imports et les mises à jour. Ce script est uniquement utile
  pour créer une base vierge pour le développement. Il nécessite d'avoir au
  préalable téléchargé le dernier fichier _stock_ Sirene des établissements
  (version géo).

- `import-sirene.sql` importe les 11 millions d'enregistrements de la base
  Sirene (toutes les entreprises françaises), la table est uniquement utile pour
  compléter les informations sur les transporteurs au moment de l'import. Les
  informations de raison sociale, code APE, adresse, etc sont issues de cette
  base. Il faut au préalable télécharger la base de données complète au format
  CSV (cf notes dans le script).

- `download_sirene` (Django) analyse le site Sirene et télécharge les mises à jour
  quotidiennes qui ne l'ont pas encore été.

- `import_sirene` (Django) importe tous les établissements de la base Sirene
  après avoir supprimé l'ancienne table.

- `download_registre` (Django) télécharge la dernière version du registre des transports
  de marchandise et créé une entrée en base de données.

- `import_registre` (Django) importe les entreprises inscrites au registre du commerce
  dans une table spécifique. Les informations sur les licences (LC, LTI),
  numéro, dates de validité, nombre ainsi que le gestionnaire sont issues de
  cette table. En cas de succès, le téléchargement est marqué comme appliqué
  dans la base de données.

- `update-carrier.sql` met à jour la table carrier en insérant tous
  les enregistrements de la table registre étendus si possible avec les
  informations de la base Sirene. Les transporteurs non présents dans la
  registre sont marqués comme supprimés. La table carrier est la table
  socle de l'application A Dock. Elle est l'agrégation des tables `registre` et
  `sirene` et permet aux utilisateurs d'y ajouter des informations
  complémentaires (téléphone, adresse e-mail, aire de travail,
  départements couverts, etc).

- `import_objectif_co2` (Django) reçoit en argument le fichier Excel de la liste
  des entreprises **labellisées** de le section Transport de marchandises de la
  page http://www.objectifco2.fr/index/documents#categ-6.

- `parse_nginx_log` (Django) analyse les logs nginx pour extraires des
  statistiques sur l'utilisation de l'application (nombre de fiches consultées,
  attestations téléchargées, etc). Ces statistiques sont stockées en base de
  données et publiées via l'API à l'interface graphique des statistiques.

## Dépendances

- [Django][django] v2
- [Python 3][python] v3.5+
- [PostgreSQL][postgresql] v9.6+

[django]: https://www.djangoproject.com/
[python]: https://www.python.org/
[postgresql]: https://www.postgresql.org/

## Tests

Pour lancer les tests en local, installer les dépendances du projet dans un
virtualenv et lancer la commande Django :

```shell
pip install -r requirements_dev.txt
./manage.py test
```

Il est aussi possible de lancer les tests via Docker avec :

`docker-compose run web`

Le projet utilise le service d'intégration continu de [CircleCI](https://circleci.com/gh/MTES-MCT/adock-api).

Les codes de modification sont envoyés par message électronique à l'utilisateur pour les recevoir en développement, vous pouvez lancer un serveur fictif avec :

`python3 -m smtpd -n -c DebuggingServer localhost:1025`

## Versions

Les numéros de version sont gérés par [bumpversion](https://github.com/peritus/bumpversion).
Le développement s'effectue sur la branche `master` et seule la branche `prod` est déployée en production.

## API

L'API est décrite au format OpenAPI v3, la documentation est publiée sur
[swaggerHub](https://app.swaggerhub.com/apis/stephaner/adock/1.0.0-oas3) et le
fichier YAML correspondant est enregistré dans le fichier `docs/openapi.yaml`.

## Format JSON

Les réponses JSON contiennent les valeurs demandées à la racine de la réponse
dans un champ nommé en fonction de la ressource :

```json
{
  "carrier": {
    "enseigne": "foo"
  }
}
```

Les validations de formulaires retournent les erreurs dans un champ `errors` qui
contient les différents champs concernés et une liste d'erreurs pour chacun
d'eux. Quand les erreurs sont globales, elles sont ajoutées à la liste du champ
spécial `__all__`, par exemple :

```json
{
  "errors": {
    "__all__": ["L'identifiant et le mot de passe sont incorrects."],
    "email": ["Ce champ est requis."]
  }
}
```

Le champ `message` est souvent retourné pour expliciter en français la raison de
la réponse en cas de succès ou erreur.
