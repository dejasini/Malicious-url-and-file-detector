import joblib

model = joblib.load("url_model.pkl")
vectorizer = joblib.load("vectorizer.pkl")

urls = [
    "https://google.com",
    "https://github.com",
    "http://free-prize-money.xyz",
    "http://secure-login-alert.ru"
]

for url in urls:
    vec = vectorizer.transform([url])
    prediction = model.predict(vec)[0]
    print(url, "→", prediction)
