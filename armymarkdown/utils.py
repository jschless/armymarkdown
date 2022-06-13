branch_to_abbrev = {
    "Adjutant General": "AG",
    "Air Defense Artillery": "AD",
    "Armor": "AR",
    "Aviation": "AV",
    "Chemical Corps": "CM",
    "Civil Affairs": "CA",
    "Corps of Engineers": "EN",
    "Field Artillery": "FA",
    "Finance Corps": "FI",
    "Functional Area": "FA",
    "Infantry": "IN",
    "Medical Service": "MS",
    "Military Intelligence": "MI",
    "Military Police": "MP",
    "Ordnance": "OD",
    "Psychological Operations": "PO",
    "Quartermaster Corps": "QM",
    "Signal Corps": "SC",
    "Special Forces": "SF",
    "Transportation": "TC",
}

abbrev_to_branch = {v: k for k, v in branch_to_abbrev.items()}

key_converter = {
    "ORGANIZATION_NAME": "unit_name",
    "ORGANIZATION_STREET_ADDRESS": "unit_street_address",
    "ORGANIZATION_CITY_STATE_ZIP": "unit_city_state_zip",
    "OFFICE_SYMBOL": "office_symbol",
    "DATE": "todays_date",
    "AUTHOR": "author_name",
    "RANK": "author_rank",
    "BRANCH": "author_branch",
    "TITLE": "author_title",
    "MEMO_TYPE": "memo_type",
    "SUBJECT": "subject",
}

inv_key_converter = {v: k for k, v in key_converter.items()}
