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


def main(blobTriggerTest: func.InputStream,inputBlob: func.InputStream,outputBlob: func.Out[func.InputStream]):

    blob_bytes = inputBlob.read()
    blob_to_read = BytesIO(blob_bytes)
    #read csv file to the pandas table
    df_rules = pd.read_csv(blob_to_read)
    #get info about the table
    df_rules.info()
    ##logging.info(df_rules.info())
    #first 5 row of the table
    ##logging.info(df_rules.head())
    #create a subset of dataframe from the 'Lemma' till the last column with alternatives '3rd_party_alternatives'
    df_rules=df_rules.loc[:, 'Lemma':'3rd_party_alternatives']
    #check new table
    ##logging.info(df_rules.info())
    #check fisrts 5 rows of the table
    ##logging.info(df_rules.head())
    #check the number of columns
    ##logging.info(len(list(df_rules.columns)))
    list_word = []

    list_word_type = []
    list_priority = []
    list_category = []
    list_primary_subcategory = []
    list_secondary_subcategory = []
    list_alt_field= []
    list_alt_sg_replacement = []
    list_alt_sg_people_first = []
    list_alt_sg_reframed = []
    list_alt_pl_collective_noun = []
    list_alt_pl = []
    list_alt_pl_people_first = []
    list_alt_pl_reframed = []
    list_3rd_party_alternatives = []

    logging.info("fine by now")
    for index, row in df_rules.iterrows():
        word = row["Lemma"]
        span = re.search("-", word)
        #only merge and split words if they are two, for example risk-taker (two words: risk and taker)
        if type(span) == re.Match and len(word.rsplit("-"))==2:
            #merge words by "-"
            list_word.append(word.rsplit("-")[0]+word.rsplit("-")[1].lower())
            list_word_type.append(row["Word_Type"])
            list_priority.append(row["Priority"])
            list_category.append(row["Category"])
            list_primary_subcategory.append(row["Primary_subcategory"])
            list_secondary_subcategory.append(row["Secondary_subcategory"])
            list_alt_field.append(row["Alt_Field"])
            list_alt_sg_replacement.append(row["Alt_Sg_Replacement"])
            list_alt_sg_people_first.append(row["Alt_Sg_people_first"])
            list_alt_sg_reframed.append(row["Alt_Sg_reframed"])
            list_alt_pl_collective_noun.append(row["Alt_Pl_collective_noun"])
            list_alt_pl.append(row["Alt_Pl"])
            list_alt_pl_people_first.append(row["Alt_Pl_people_first"])
            list_alt_pl_reframed.append(row['Alt_Pl_reframed'])
            list_3rd_party_alternatives.append(row["3rd_party_alternatives"])
            
            
            
            #split words by "-"  
            list_word.append(word.rsplit("-")[0]+" "+word.rsplit("-")[1])
            list_word_type.append(row["Word_Type"])
            list_priority.append(row["Priority"])
            list_category.append(row["Category"])
            list_primary_subcategory.append(row["Primary_subcategory"])
            list_secondary_subcategory.append(row["Secondary_subcategory"])
            list_alt_field.append(row["Alt_Field"])
            list_alt_sg_replacement.append(row["Alt_Sg_Replacement"])
            list_alt_sg_people_first.append(row["Alt_Sg_people_first"])
            list_alt_sg_reframed.append(row["Alt_Sg_reframed"])
            list_alt_pl_collective_noun.append(row["Alt_Pl_collective_noun"])
            list_alt_pl.append(row["Alt_Pl"])
            list_alt_pl_people_first.append(row["Alt_Pl_people_first"])
            list_alt_pl_reframed.append(row['Alt_Pl_reframed'])
            list_3rd_party_alternatives.append(row["3rd_party_alternatives"])
            

    #NEW  from the bunch of created lists create a dataframe
    data = pd.DataFrame(list(zip(list_word,list_word_type,list_priority, list_category, list_primary_subcategory, list_secondary_subcategory, 
    list_alt_field, list_alt_sg_replacement, list_alt_sg_people_first, list_alt_sg_reframed, list_alt_pl_collective_noun,
    list_alt_pl, list_alt_pl_people_first, list_alt_pl_reframed, list_3rd_party_alternatives)), columns=list(df_rules.columns))

    # check number of columns in the new dataframe
    ##logging.info(len(data.columns))

    #list of names of the columns
    data_columns = list(data.columns)
    df_rules_columns = list(df_rules.columns)

    for name1, name2 in zip(df_rules_columns, data_columns):
        if name1!=name2:
            logging.info(name1, name2)
        else:
            logging.info("correct")

    #check first 5 rows of the new dataframe
    ##logging.info(data.head())

    #check the last 5 rows of the new dataframe
    ##logging.info(data.tail())

    # check info about new dataframe
    ##logging.info("New dataframe: %s" % data.info())

    #original dataframe
    ##logging.info(df_rules.info())

    #merge two dataframes
    df_fin = df_rules.append(data, ignore_index = True)

    #check info about merged dataframe
    ##logging.info(df_fin.info())

    df_sorted = df_fin.sort_values(by=['Lemma'], inplace=False, ascending=True)

    ##logging.info(df_sorted.info())

    df_sorted[df_sorted["Lemma"]=="must have"]

    #get index of false positives
    i = df_sorted[((df_sorted.Lemma == 'must have'))].index

    #drop rows with false positives
    df_sorted = df_sorted.drop(i)

    #save to csv file after preprocessing
    output = df_sorted.to_csv(index=False)
    outputBlob.set(output)
    #test read of dataframe
    ##blob_bytes_out = inputBlob2.read()
    ##blob_to_read_out = BytesIO(blob_bytes_out)
    ##df_test = pd.read_csv(blob_to_read_out )

    #check info
    ##logging.info(df_test.info())
    #check first 5 rows 
    ##logging.info(df_test.head())

    #outputs = df_rules.to_csv(index = False)
    #logging.info("Python blob trigger function")
    #logging.info("outputs %s" % outputs)            
    

