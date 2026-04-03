import pandas as pd

# =============================
# LOAD YOUR CURRENT DATASET
# =============================

df = pd.read_csv("final_urls_dataset.csv")

# Ensure proper format
df.columns = ["url", "label"]
df["label"] = df["label"].str.lower().str.strip()

print("Original Distribution:")
print(df["label"].value_counts())

# =============================
# ADD REAL SAFE DOMAINS
# =============================

real_safe_domains = [
    "google.com",
    "github.com",
    "microsoft.com",
    "linkedin.com",
    "apple.com",
    "stackoverflow.com",
    "wikipedia.org",
    "oracle.com",
    "adobe.com",
    "salesforce.com",
    "tesla.com",
    "nvidia.com",
    "ibm.com"
]

# Replicate many times to make impact
real_safe_df = pd.DataFrame({
    "url": real_safe_domains * 10000,
    "label": "safe"
})

# =============================
# MERGE WITH ORIGINAL
# =============================

df = pd.concat([df, real_safe_df])

# Shuffle dataset
df = df.sample(frac=1, random_state=42).reset_index(drop=True)

print("\nImproved Distribution:")
print(df["label"].value_counts())

# Save new dataset
df.to_csv("improved_urls_dataset.csv", index=False)

print("\nImproved dataset saved successfully.")
