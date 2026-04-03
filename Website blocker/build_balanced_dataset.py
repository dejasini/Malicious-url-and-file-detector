import pandas as pd
import random
import string

print("Loading malicious dataset...")
df_mal = pd.read_csv("malicious_phish.csv")
df_mal.columns = df_mal.columns.str.lower()
df_mal = df_mal[['url']]
df_mal['label'] = 'malicious'

# Downsample malicious to 50,000 samples
df_mal = df_mal.sample(n=50000, random_state=42)

print("Generating realistic safe URLs...")

def random_domain():
    name = ''.join(random.choices(string.ascii_lowercase, k=8))
    tld = random.choice([".com", ".org", ".net", ".edu", ".gov"])
    return f"https://www.{name}{tld}"

safe_urls = [random_domain() for _ in range(50000)]

df_safe = pd.DataFrame({
    "url": safe_urls,
    "label": "safe"
})

# Combine
df_final = pd.concat([df_mal, df_safe], ignore_index=True)

# Shuffle
df_final = df_final.sample(frac=1, random_state=42).reset_index(drop=True)

df_final.to_csv("final_urls_dataset.csv", index=False)

print("Balanced dataset created!")
print(df_final['label'].value_counts())

