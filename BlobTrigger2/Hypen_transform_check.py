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


def main(blobTrigger2: func.InputStream,inBlob: func.InputStream):
    #test read of dataframe
    blob_bytes_out = inBlob.read()
    blob_to_read_out = BytesIO(blob_bytes_out)
    df_test = pd.read_csv(blob_to_read_out )

    #check info
    logging.info(df_test.info())
    #check first 5 rows 
    logging.info(df_test.head())

    #outputs = df_rules.to_csv(index = False)
    #logging.info("Python blob trigger function")
    #logging.info("outputs %s" % outputs)            
    

