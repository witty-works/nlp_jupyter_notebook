import logging
import pandas as pd
import azure.functions as func
import re
import csv
import json
import os
import sys
import requests
from io import BytesIO
def get_data_from_files(locale, inblob: func.InputStream):
    all_alternatives = []
    all_triggers = []
    all_alternative_groups = []
    logging.info(inblob)
    blob_bytes = inblob.read()
    blob_to_read = BytesIO(blob_bytes)
    df = pd.read_csv(blob_to_read)
    #training_data_path = blob_to_read
    #with open(training_data_path) as f:
    #reader = csv.DictReader(blob_to_read)
    #column_names = reader.fieldnames
    #if "Alt_split" in column_names:
    for index, row in df.iterrows():
        value = row["Alt_split"]
        value = value.replace("'", '"')
        try:
            all_alternative_groups += json.loads(value)
        except ValueError:
            continue

        if row["Primary_subcategory"] not in ["function", "titles"]:
            value = row["Lemma"]
            value = value.replace("'", '"')
            all_triggers.append(value)

    for all_alternative_group in all_alternative_groups:
        all_alternatives.extend(all_alternative_group.split("|"))

    return set(all_triggers), set(all_alternatives)



def main(inblob: func.InputStream):
    locale = "en"
    all_triggers, all_alternatives = get_data_from_files(locale, inblob)
    logging.info(all_alternatives)