import pandas as pd
import joblib
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report

# Load dataset
data = pd.read_csv("improved_urls_dataset.csv")

# Clean
data = data.dropna()
data = data.sample(frac=1, random_state=42).reset_index(drop=True)

print(data["label"].value_counts())

# Features and target
X = data["url"]
y = data["label"]

# Split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# Vectorize
vectorizer = TfidfVectorizer(analyzer="char", ngram_range=(3,5))
X_train_vec = vectorizer.fit_transform(X_train)
X_test_vec = vectorizer.transform(X_test)

# Model
model = LogisticRegression(max_iter=2000)
model.fit(X_train_vec, y_train)

# Evaluation
print("Cross Validation Accuracy:",
      cross_val_score(model, X_train_vec, y_train, cv=5).mean())

print("Test Accuracy:", model.score(X_test_vec, y_test))

print(classification_report(y_test, model.predict(X_test_vec)))

# Save
joblib.dump(model, "url_model.pkl")
joblib.dump(vectorizer, "vectorizer.pkl")

print("Model saved successfully.")
