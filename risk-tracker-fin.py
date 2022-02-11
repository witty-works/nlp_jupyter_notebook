# NLP library
import pandas as pd
import spacy

# Regular expression library
import re
import ast

# Model data
model = {"en": spacy.load("en_core_web_sm"), "de": spacy.load("de_core_news_sm")}

#pattern to search "-"
p = re.compile(".*-", re.IGNORECASE)

df_rules = pd.read_csv("rules_15NOV_German.csv")

len(list(df_rules.columns))