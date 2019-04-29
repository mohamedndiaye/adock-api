#!/bin/sh

output="csv/greco.csv"
files=(
  Auvergne_Rhone_Alpes.csv
  Bourgogne_Franche_Comte.csv
  Bretagne.csv
  Centre_Val_de_Loire.csv
  Corse.csv
  Grand_Est.csv
  Hauts_de_France.csv
  IDF.csv
  Normandie.csv
  Nouvelle_Aquitaine.csv
  Occitanie.csv
  Pays_de_la_Loire.csv
  Provence__Alpes_Cote_d_azur.csv
)


echo "Registre,No siren ou provisoire,Raison sociale,Localisation,Code postal,Ville,Dept,Telephone,Mail,Inscription activite,Date dernier bilan,Capitaux propres,Import finance (oui/non),Regime derogatoire,Motif derogation,Type licence,Date fin validite,Copies valides,Copies non valides" > $output
for f in ${files[@]}; do
    echo "Append $f to $output"
    # Remove each header and concat
    sed -e "1d" csv/$f >> $output
done

echo "Convert $output to Unix and UTF-8"
dos2unix $output
iconv --from-code=ISO-8859-1 --to-code=UTF-8 < $output > tmp
mv tmp $output

echo "Fix trailing comma in $output"
LC_ALL=C sed -e 's/,$//' < $output > tmp
mv tmp $output

exit 0
