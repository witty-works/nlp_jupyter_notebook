import logging
import azure.functions as func
import json
    # NLP library
import pandas as pd
import spacy

# Regular expression library
import re
import ast
from io import BytesIO, StringIO
from azure.storage.blob import BlobServiceClient


def main(blobTriggerTest: func.InputStream,inputBlob: func.InputStream, outputBlob: func.Out[func.InputStream]):
    #logging.info(f"Python blob trigger function processed blob \n")


    # Model data
    model = {"en": spacy.load("en_core_web_sm"), "de": spacy.load("de_core_news_sm")}

    """with open("test2.csv", "b") as my_blob:
        blob_data = blob_client_instance.download_blob()
        blob_data.readinto(my_blob)"""

    blob_bytes = inputBlob.read()
    blob_to_read = BytesIO(blob_bytes)
    df = pd.read_csv(blob_to_read)
    print("Length of the csv file:" + str(len(df.index)))

    outputs = df.to_csv(index = False)
    logging.info("Python blob trigger function")
    logging.info("outputs %s" % outputs)            
    outputBlob.set(outputs)

    #df = pd.read_csv('test2.csv')
    #df.to_csv("df_new.csv", index=False)
    #outputBlob.set("df_new.csv")
    #blobstring = blob_service.get_blob_to_text('input-witty-rules', 'test.csv')
    #print(blobstring)
    #logging.info(blobstring)
    #df = pd.read_csv(StringIO(blobstring))

    #df.to_csv("df_new.csv", index=False)
    #outputBlob.set("df_new.csv")
    #pattern to search "-"
    """
    blob_bytes = inputBlob.read()
    blob_to_read = BytesIO(blob_bytes)
    df = pd.read_csv(blob_to_read)
    """