import pandas as pd
import joblib
import re

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.metrics import classification_report, accuracy_score

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
# Train Test Split
# -----------------------------
X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

# -----------------------------
# TF-IDF
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
print("\nTraining Logistic Regression...")
log_model = LogisticRegression(max_iter=1000)
log_model.fit(X_train_vec, y_train)

log_pred = log_model.predict(X_test_vec)

print("\n--- Logistic Regression Results ---")
print("Accuracy:", accuracy_score(y_test, log_pred))
print(classification_report(y_test, log_pred))


# =============================
# 2️⃣ Linear SVM
# =============================
print("\nTraining Linear SVM...")
svm_model = LinearSVC()
svm_model.fit(X_train_vec, y_train)

svm_pred = svm_model.predict(X_test_vec)

print("\n--- Linear SVM Results ---")
print("Accuracy:", accuracy_score(y_test, svm_pred))
print(classification_report(y_test, svm_pred))


# =============================
# Save Best Model
# =============================
log_acc = accuracy_score(y_test, log_pred)
svm_acc = accuracy_score(y_test, svm_pred)

if svm_acc > log_acc:
    print("\nSVM performed better. Saving SVM model.")
    joblib.dump(svm_model, "url_model.pkl")
else:
    print("\nLogistic Regression performed better. Saving Logistic model.")
    joblib.dump(log_model, "url_model.pkl")

joblib.dump(vectorizer, "vectorizer.pkl")

print("\nModel training complete and best model saved.")
