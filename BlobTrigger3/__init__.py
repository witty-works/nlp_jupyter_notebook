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
from azure.storage.blob import BlobServiceClient
from azure.storage.blob import BlobClient


api_url = "http://localhost:8081/v2/check"


def intersection(lst1, lst2):
    return list(set(lst1) & set(lst2))


def get_data_from_files(locale, inblob: func.InputStream):
    all_alternatives = []
    all_triggers = []
    all_alternative_groups = []
    # logging.info(inblob)
    blob_bytes = inblob.read()
    blob_to_read = BytesIO(blob_bytes)
    df = pd.read_csv(blob_to_read)
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


def generate_alternatives_english(all_alternatives):
    all_words = []
    clean_words = []

    for word in all_alternatives:
        all_words.extend(word.split())

    for word in all_words:
        for ch in ["(", ")", ".", "^", ","]:
            if ch in word:
                word = word.replace(ch, "")
        if "/" in word:
            clean_words.extend(word.split("/"))
        elif len(word) >= 1:
            clean_words.append(word)

    return set(clean_words)


def print_trigger_alternative_overlap(locale, all_triggers, words):
    print("Trigger words, overlapping with alternatives for locale: " + locale)
    print(intersection(all_triggers, words))


def check_word(word, locale):
    response = requests.post(
        api_url,
        data={
            "text": word,
            "language": locale,
            "motherTongue": locale,
        },
    )

    if response.status_code != 200:
        print("Got error on: " + word)

    if not response.json()["matches"]:
        return False

    return True


def check_words_spelling(words, current_words):
    words_to_write = []

    for locale in words:
        for word in words[locale]:
            if len(word) < 3 or word in current_words:
                continue

            add_word = True
            if api_url and word not in current_words:
                add_word = check_word(word, locale)

            if add_word:
                words_to_write.append(word)
    return set(words_to_write)


def append_original_ignored_words(
    path_to_ignore_file,
    current_words,
    words_to_write,
    outblob: func.Out[func.InputStream],
):
    connect_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")

    blob_service_client = BlobServiceClient.from_connection_string(connect_str)

    blob_client2 = blob_service_client.get_blob_client(
        container="output-witty-rules", blob="ignore_out.txt"
    )
    # maybe just a list? with current and new words (append)
    # output_words = "\n".join(current_words)
    words_to_write = sorted(words_to_write, key=str.casefold)
    words_to_write.extend(current_words)
    output_words = "\n".join(words_to_write)
    blob_client2.upload_blob(output_words)


def get_current_words(original_languagetool_path, ignore_languagetool_path):

    connect_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")

    blob_service_client = BlobServiceClient.from_connection_string(connect_str)
    container_client = blob_service_client.get_container_client("output-witty-rules")
    blob_client = container_client.get_blob_client("ignore.txt")
    blobstr = blob_client.download_blob().content_as_text(
        max_concurrency=1, encoding="UTF-8"
    )
    current_words = blobstr.split()

    logging.info(current_words)
    return current_words


def update_ignore_file(
    words,
    original_languagetool_path,
    path_to_ignore_file,
    outblob: func.Out[func.InputStream],
):

    current_words = get_current_words(original_languagetool_path, path_to_ignore_file)
    words_to_write = check_words_spelling(words, current_words)
    append_original_ignored_words(
        path_to_ignore_file, current_words, words_to_write, outblob
    )


def main(inblob: func.InputStream, outblob: func.Out[func.InputStream]):
    locales = ["en-US"]
    words = {}
    for locale in locales:
        all_triggers, all_alternatives = get_data_from_files(locale, inblob)

        words[locale] = generate_alternatives_english(all_alternatives)

        print_trigger_alternative_overlap(locale, all_triggers, words[locale])
    path_to_ignore_file = "ignore.txt"
    original_languagetool_path = ""

    update_ignore_file(words, original_languagetool_path, path_to_ignore_file, outblob)
