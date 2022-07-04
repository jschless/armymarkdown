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
    "FOR_ORGANIZATION_NAME": "for_unit_name",
    "FOR_ORGANIZATION_STREET_ADDRESS": "for_unit_street_address",
    "FOR_ORGANIZATION_CITY_STATE_ZIP": "for_unit_city_state_zip",
    "THRU_ORGANIZATION_NAME": "thru_unit_name",
    "THRU_ORGANIZATION_STREET_ADDRESS": "thru_unit_street_address",
    "THRU_ORGANIZATION_CITY_STATE_ZIP": "thru_unit_city_state_zip",
}

inv_key_converter = {v: k for k, v in key_converter.items()}

optional_keys = set(
    [
        "for_unit_name",
        "for_unit_street_address",
        "for_unit_city_state_zip",
        "thru_unit_name",
        "thru_unit_street_address",
        "thru_unit_city_state_zip",
        "suspense_date",
        "document_mark",
        "enclosures",
        "distros",
        "cfs",
        "document_mark",
        "todays_date",
    ]
)

list_keys = set(
    [
        "for_unit_name",
        "for_unit_street_address",
        "for_unit_city_state_zip",
        "thru_unit_name",
        "thru_unit_street_address",
        "thru_unit_city_state_zip",
        "enclosures",
        "distros",
        "cfs",
    ]
)
