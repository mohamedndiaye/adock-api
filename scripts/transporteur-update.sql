begin;

-- Reset the values before the update
update transporteur
   set lower_than_3_5_licenses = 0,
       greater_than_3_5_licenses = 0;

-- Update the current number of licenses for merchandise (travelers are excluded)
-- Fast but a seq scan is used (create partial index?)
update transporteur as t
   set lower_than_3_5_licenses = case when g.licence = 'LCM'
                                      then g.copies_valides
                                      else lower_than_3_5_licenses
                                  end,
       greater_than_3_5_licenses = case when g.licence = 'LTIM'
                                        then g.copies_valides
                                        else greater_than_3_5_licenses
                                    end
  from greco as g
 where t.siret::char(9) = g.siren;

commit;
