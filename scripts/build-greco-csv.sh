#!/bin/sh

files=(
    Auvergne_Rhone_Alpes.csv
    Bourgogne_franche_comte.csv
    Bretagne.csv
    Centre_Val_de_Loire.csv
    Corse.csv
    Grand_est.csv
    Hauts_de_france.csv
    Normandie.csv
    Nouvelle_Aquitaine.csv
    Occitanie.csv
    Pays_de_la_loire.csv
    Provence_alpes_cotes_azur.csv
#   This file isn't consistent
#    idf-fixed.csv
)

# This one has a remaining '| on each line :(
#LC_ALL=C sed -e 's/|.$//' < idf.csv > idf-fixed.csv

# Replace bad original header :(
echo '"Registre"|"No siren ou provisoire"|"Raison sociale"|"Localisation"|"Code postal"|"Ville"|"Dept"|"Telephone"|"Mail"|"Inscription activite"|"Date dernier bilan"|"Capitaux propres"|"Import finance (oui/non)"|"Regime derogatoire"|"Motif derogation"|"Type licence"|"Date fin validite"|"Copies valides"|"Copies non valides"' > greco.csv

rm greco.csv
for f in ${files[@]}; do
    # Remove each header and concat
    sed -e "1d" $f >> greco.csv
done

dos2unix greco.csv
iconv --from-code=ISO-8859-1 --to-code=UTF-8 < greco.csv > tmp
mv tmp greco.csv

exit 0
