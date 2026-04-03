import pandas as pd
import joblib
import re
import json

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

print("Loading dataset...")
df = pd.read_csv("final_urls_dataset.csv")

# -----------------------------
# Clean URLs
# -----------------------------
def clean_url(url):
    url = str(url).lower()
    url = re.sub(r'https?://', '', url)
    url = re.sub(r'www\.', '', url)
    return url

df['url'] = df['url'].apply(clean_url)

X = df['url']
y = df['label']

# -----------------------------
# Train-Test Split
# -----------------------------
X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

# -----------------------------
# TF-IDF Vectorizer
# -----------------------------
vectorizer = TfidfVectorizer(
    ngram_range=(1,3),
    max_features=15000
)

X_train_vec = vectorizer.fit_transform(X_train)
X_test_vec = vectorizer.transform(X_test)

# =============================
# 1️⃣ Logistic Regression
# =============================
log_model = LogisticRegression(max_iter=1000)
log_model.fit(X_train_vec, y_train)
log_pred = log_model.predict(X_test_vec)

log_acc = accuracy_score(y_test, log_pred)

# =============================
# 2️⃣ Linear SVM
# =============================
svm_model = LinearSVC()
svm_model.fit(X_train_vec, y_train)
svm_pred = svm_model.predict(X_test_vec)

svm_acc = accuracy_score(y_test, svm_pred)

# =============================
# 3️⃣ Random Forest
# =============================
rf_model = RandomForestClassifier(
    n_estimators=100,
    random_state=42
)

rf_model.fit(X_train_vec, y_train)
rf_pred = rf_model.predict(X_test_vec)

rf_acc = accuracy_score(y_test, rf_pred)

# =============================
# Print Results
# =============================
print("\n--- Logistic Regression ---")
print("Accuracy:", log_acc)

print("\n--- Linear SVM ---")
print("Accuracy:", svm_acc)

print("\n--- Random Forest ---")
print("Accuracy:", rf_acc)

# =============================
# Save Metrics
# =============================
metrics = {
    "logistic": {
        "accuracy": log_acc,
        "precision": precision_score(y_test, log_pred, pos_label="malicious"),
        "recall": recall_score(y_test, log_pred, pos_label="malicious"),
        "f1": f1_score(y_test, log_pred, pos_label="malicious")
    },
    "svm": {
        "accuracy": svm_acc,
        "precision": precision_score(y_test, svm_pred, pos_label="malicious"),
        "recall": recall_score(y_test, svm_pred, pos_label="malicious"),
        "f1": f1_score(y_test, svm_pred, pos_label="malicious")
    },
    "random_forest": {
        "accuracy": rf_acc,
        "precision": precision_score(y_test, rf_pred, pos_label="malicious"),
        "recall": recall_score(y_test, rf_pred, pos_label="malicious"),
        "f1": f1_score(y_test, rf_pred, pos_label="malicious")
    }
}

with open("model_metrics.json", "w") as f:
    json.dump(metrics, f)

# =============================
# Save Best Model
# =============================
best_model_name = max(
    metrics,
    key=lambda x: metrics[x]["f1"]
)

print("\nBest model based on F1-score:", best_model_name)

if best_model_name == "logistic":
    joblib.dump(log_model, "url_model.pkl")
elif best_model_name == "svm":
    joblib.dump(svm_model, "url_model.pkl")
else:
    joblib.dump(rf_model, "url_model.pkl")

joblib.dump(vectorizer, "vectorizer.pkl")

print("\nBest model saved successfully.")

