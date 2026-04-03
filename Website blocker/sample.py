import pandas as pd

df = pd.read_csv("final_urls_dataset.csv")

print(df["label"].value_counts())
print(df["label"].unique())
