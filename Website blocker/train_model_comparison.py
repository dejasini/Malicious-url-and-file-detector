import pandas as pd
import joblib
import re
import json
import os
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    roc_curve,
    auc
)
from sklearn.preprocessing import label_binarize

os.makedirs("static/analytics", exist_ok=True)

print("Loading dataset...")
df = pd.read_csv("final_urls_dataset.csv")

# Clean URL
def clean_url(url):
    url = str(url).lower()
    url = re.sub(r'https?://', '', url)
    url = re.sub(r'www\.', '', url)
    return url

df['url'] = df['url'].apply(clean_url)

X = df['url']
y = df['label']

# Train/Test split
X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

# TF-IDF
vectorizer = TfidfVectorizer(
    ngram_range=(1,3),
    max_features=15000
)

X_train_vec = vectorizer.fit_transform(X_train)
X_test_vec = vectorizer.transform(X_test)

# Models
models = {
    "Logistic Regression": LogisticRegression(max_iter=1000),
    "Linear SVM": LinearSVC(),
    "Random Forest": RandomForestClassifier(n_estimators=100, random_state=42)
}

metrics = {}

for name, model in models.items():
    print(f"\nTraining {name}...")
    model.fit(X_train_vec, y_train)
    y_pred = model.predict(X_test_vec)

    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, pos_label="malicious")
    rec = recall_score(y_test, y_pred, pos_label="malicious")
    f1 = f1_score(y_test, y_pred, pos_label="malicious")

    metrics[name] = {
        "accuracy": acc,
        "precision": prec,
        "recall": rec,
        "f1": f1
    }

    # Confusion Matrix
    cm = confusion_matrix(y_test, y_pred)
    plt.figure()
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues")
    plt.title(f"{name} - Confusion Matrix")
    plt.xlabel("Predicted")
    plt.ylabel("Actual")
    plt.savefig(f"static/analytics/{name}_confusion.png")
    plt.close()

    # ROC Curve (only for models that support decision function or predict_proba)
    try:
        y_bin = label_binarize(y_test, classes=["safe", "malicious"])
        if hasattr(model, "decision_function"):
            scores = model.decision_function(X_test_vec)
        else:
            scores = model.predict_proba(X_test_vec)[:, 1]

        fpr, tpr, _ = roc_curve(y_bin, scores)
        roc_auc = auc(fpr, tpr)

        plt.figure()
        plt.plot(fpr, tpr, label=f"AUC = {roc_auc:.2f}")
        plt.plot([0,1], [0,1], linestyle='--')
        plt.title(f"{name} - ROC Curve")
        plt.xlabel("False Positive Rate")
        plt.ylabel("True Positive Rate")
        plt.legend()
        plt.savefig(f"static/analytics/{name}_roc.png")
        plt.close()

    except:
        pass

    # Cross-validation
    cv_scores = cross_val_score(model, X_train_vec, y_train, cv=5)
    metrics[name]["cross_val_mean"] = cv_scores.mean()

# Save metrics
with open("model_metrics.json", "w") as f:
    json.dump(metrics, f)

# Choose best model by F1
best_model = max(metrics, key=lambda x: metrics[x]["f1"])
print("\nBest Model:", best_model)

joblib.dump(models[best_model], "url_model.pkl")
joblib.dump(vectorizer, "vectorizer.pkl")

print("\nAll experiments completed and best model saved.")
