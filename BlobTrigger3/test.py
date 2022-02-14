import pandas as pd
import json
df = pd.read_csv("gendered_no_noun_words.csv")
all_alternatives = []
all_alternative_groups = []
all_triggers = []
for index, row in df.iterrows():
        print(row)
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
print(set(all_triggers), set(all_alternatives))
