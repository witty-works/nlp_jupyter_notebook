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


def generate_used_words_list(path_to_ignore_file):
    used_words = []

    with open(path_to_ignore_file, "r") as readfile:
        used_words = [
            line.strip().replace("\/", "/").replace("\_", "_") for line in readfile
        ]

    print("Previously used words: " + str(len(used_words)))
    return used_words


def check_word(word, locale):
    response = requests.post(
        api_url,
        data={
            "text": word,
            "language": locale,
            "motherTongue": locale,
        },
    )
    # logging.info(response)
    if response.status_code != 200:
        print("Got error on: " + word)

    if not response.json()["matches"]:
        return False

    return True


def check_words_spelling(words, current_words, used_words):
    words_to_write = []

    for locale in words:
        for word in words[locale]:
            if len(word) < 3 or word in current_words:
                continue

            add_word = True
            if api_url and word not in used_words:
                add_word = check_word(word, locale)

            if add_word:
                words_to_write.append(word)
    return set(words_to_write)


def add_words_to_ignore(path_to_ignore_file, words_to_write):
    # connect_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    # blob_service_client = BlobServiceClient.from_connection_string(connect_str)
    words_to_write = sorted(words_to_write, key=str.casefold)
    # blob_client = blob_service_client.get_blob_client(
    #    container="output-witty-rules", blob="ignore.txt"
    # )
    connect_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    blob = BlobClient.from_connection_string(
        conn_str=connect_str,
        container_name="output-witty-rules",
        blob_name="ignore.txt",
    )
    with open("ignore.txt", "wb") as my_blob:
        blob_data = blob.download_blob()
        for word in words_to_write:
            word = word.replace("/", "\/")
            word = word.replace("_", "\_")
            my_blob.write(bytes(word, "utf-8"))
            ##my_blob.write("\n")

    logging.info(blob_data)
    with open(path_to_ignore_file, "w") as f:
        for word in words_to_write:
            word = word.replace("/", "\/")
            word = word.replace("_", "\_")
            f.write(word)
            f.write("\n")
    # with open(path_to_ignore_file, "rb") as b:
    #    blob_client.upload_blob(b)


def append_original_ignored_words(
    path_to_ignore_file, current_words, outblob: func.Out[func.InputStream]
):
    connect_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    blob_service_client = BlobServiceClient.from_connection_string(connect_str)
    # words_to_write = sorted(words_to_write, key=str.casefold)
    blob_client = blob_service_client.get_blob_client(
        container="output-witty-rules", blob="ignore_out.txt"
    )
    with open(path_to_ignore_file, "a") as myfile:
        myfile.write("# Old words (added by LT): \n")
        for word in current_words:
            myfile.write(word)
            myfile.write("\n")

    with open(path_to_ignore_file, "rb") as b:
        blob_client.upload_blob(b)


def get_current_words(original_languagetool_path, ignore_languagetool_path):
    current_words = []
    if original_languagetool_path:
        with open(
            original_languagetool_path,
            "r",
        ) as f:
            lines = f.readlines()
            for line in lines:
                li = line.strip()
                if not li.startswith("#"):
                    current_words.append(li)
    else:
        start = False
        with open(
            ignore_languagetool_path,
            "r",
        ) as f:
            lines = f.readlines()
            for line in lines:
                logging.info("lines=")
                logging.info(lines)
                if start == True:
                    li = line.strip()
                    current_words.append(li)
                if line == "# Old words (added by LT): \n":
                    start = True
    logging.info(current_words)
    return current_words


def update_ignore_file(
    words,
    original_languagetool_path,
    path_to_ignore_file,
    outblob: func.Out[func.InputStream],
):
    current_words = get_current_words(original_languagetool_path, path_to_ignore_file)
    used_words = generate_used_words_list(path_to_ignore_file)
    words_to_write = check_words_spelling(words, current_words, used_words)
    # logging.info(words_to_write)
    # logging.info(words)
    # newly_added_words = intersection(words_to_write, used_words)
    # print("Newly added words: " + str(len(newly_added_words)))
    # if newly_added_words and len(newly_added_words) < 20:
    #    print(newly_added_words)

    add_words_to_ignore(path_to_ignore_file, words_to_write)
    append_original_ignored_words(path_to_ignore_file, current_words, outblob)


def main(inblob: func.InputStream, outblob: func.Out[func.InputStream]):
    # current_words = []
    locales = ["en-US"]
    words = {}
    for locale in locales:
        all_triggers, all_alternatives = get_data_from_files(locale, inblob)

        words[locale] = generate_alternatives_english(all_alternatives)

        print_trigger_alternative_overlap(locale, all_triggers, words[locale])

    # logging.info(all_alternatives)

    path_to_ignore_file = "ignore.txt"
    original_languagetool_path = "ignore_original.txt"

    update_ignore_file(words, original_languagetool_path, path_to_ignore_file, outblob)
