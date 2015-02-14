# Process for getting migrations from OIPAv2.1 to new OIPA

1. Get OIPAV2.1 running under Django 1.7       DONE synch to OIPA-V2.1 - git checkout migrate
2. Run ./manage.py makemigrations [app_name]
        This seems to require an app name, apps required are IATI, IATI_synchroniser, indicators, geodata and possible Cache and CurrencyConverter
3. Get new OIPA from https://github.com/openaid-IATI/OIPA 
    Delete all current migrations in the codebase
    Copy across generated initial migration directories from migrate OIPA-V2.1
    Edit those initial migrations replacing IATI with iati - indicators with indicator, Cache with cache
4. In new OIPA run ./manage.py makemigrations [app_name], follow instructions
5. Sanity Check the output
    Check basic model renames are found, not deleted and readded - look for location - Location and geodata.adm1_region geodata.Adm1Region
    Run makemigrations repeatedly, should produce `no changes found` after first run

