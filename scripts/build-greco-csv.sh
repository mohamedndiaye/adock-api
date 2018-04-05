#!/bin/sh

output=csv/greco.csv
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
    idf-fixed.csv
)

# This one has a remaining '| on each line :(
#LC_ALL=C sed -e 's/ï¿//g' < csv/idf.csv > csv/idf-fixed.csv
#LC_ALL=C sed -e 's/|.$//' < csv/idf.csv > csv/idf-fixed.csv

# Replace bad original header :(
echo '"Registre"|"No siren ou provisoire"|"Raison sociale"|"Localisation"|"Code postal"|"Ville"|"Dept"|"Telephone"|"Mail"|"Inscription activite"|"Date dernier bilan"|"Capitaux propres"|"Import finance (oui/non)"|"Regime derogatoire"|"Motif derogation"|"Type licence"|"Date fin validite"|"Copies valides"|"Copies non valides"' > $output

rm $output
for f in ${files[@]}; do
    # Remove each header and concat
    sed -e "1d" csv/$f >> $output
done

dos2unix $output
iconv --from-code=ISO-8859-1 --to-code=UTF-8 < $output > tmp
mv tmp $output

exit 0
