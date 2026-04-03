import joblib

model = joblib.load("url_model.pkl")

print(model.classes_)
