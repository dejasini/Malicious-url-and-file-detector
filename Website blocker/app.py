from flask import Flask, render_template, request, redirect, session
import mysql.connector
import joblib
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
import json
import os
from urllib.parse import urlparse\

app = Flask(__name__)
app.secret_key = "supersecretkey"
HOSTS_PATH = r"C:\Windows\System32\drivers\etc\hosts"
REDIRECT_IP = "127.0.0.1"


# ================= DATABASE =================

DB_CONFIG = {
    "host": "127.0.0.1",
    "user": "root",
    "password": "",
    "database": "1websiteblock",
    "charset": "utf8"
}


def extract_domain(url):
    parsed = urlparse(url)
    domain = parsed.netloc.lower()

    if domain.startswith("www."):
        domain = domain[4:]

    return domain

def get_db():
    return mysql.connector.connect(**DB_CONFIG)

# ================= LOAD MODEL =================

model = joblib.load("url_model.pkl")
vectorizer = joblib.load("vectorizer.pkl")
print("Loaded model classes:", model.classes_)

# ================= EMAIL =================

def send_email_alert(username, resource):
    try:
        sender = "projtempo2004@gmail.com"
        password = "rfthezmmqqbeexpk"
        admin_email = "projtempo2004@gmail.com"
        message = MIMEText(f"""
SECURITY ALERT

Employee: {username}
Blocked Resource: {resource}
Time: {datetime.now()}
""")

        message["Subject"] = "Malicious Activity Detected"
        message["From"] = sender
        message["To"] = admin_email

        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(sender, password)
        server.send_message(message)
        server.quit()

    except Exception as e:
        print("Email error:", e)

# ================= HOME =================

@app.route("/")
def index():
    return render_template("index.html")

# ================= REGISTER =================

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO regtb (username, password) VALUES (%s, %s)",
            (username, password)
        )
        db.commit()
        db.close()

        return redirect("/login")

    return render_template("register.html")

# ================= LOGIN =================

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "SELECT * FROM regtb WHERE username=%s AND password=%s",
            (username, password)
        )
        user = cursor.fetchone()
        db.close()

        if user:
            session["user"] = username
            return redirect("/employee_dashboard")

        return render_template("login.html", error="Invalid credentials")

    return render_template("login.html")

# ================= EMPLOYEE DASHBOARD =================

@app.route("/employee_dashboard")
def employee_dashboard():
    if "user" not in session:
        return redirect("/login")
    return render_template("employee_dashboard.html", username=session["user"])

def normalize_url(url):
    url = url.lower().strip()
    url = url.replace("http://", "")
    url = url.replace("https://", "")
    url = url.replace("www.", "")
    return url

# ================= BLOCK DOMAIN =================

def block_domain(domain):
    try:
        with open(HOSTS_PATH, "r+") as file:
            content = file.read()

            entries = [
                f"{REDIRECT_IP} {domain}",
                f"{REDIRECT_IP} www.{domain}"
            ]

            for entry in entries:
                if entry not in content:
                    file.write(f"\n{entry}")

        os.system("ipconfig /flushdns")
        print(f"[+] Blocked externally: {domain}")

    except Exception as e:
        print("Hosts block error:", e)

# ================= UNBLOCK DOMAIN =================

def unblock_domain(domain):
    try:
        with open(HOSTS_PATH, "r+") as file:
            lines = file.readlines()
            file.seek(0)

            for line in lines:
                if domain not in line:
                    file.write(line)

            file.truncate()

        print(f"[+] Unblocked externally: {domain}")

    except Exception as e:
        print("Hosts unblock error:", e)

# ================= URL SCAN =================

@app.route("/scan_url", methods=["GET", "POST"])
def scan_url():

    if "user" not in session:
        return redirect("/login")

    if request.method == "POST":

        url = request.form["url"].strip().lower()

        # Force http prefix if missing
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "http://" + url

        db = get_db()
        cursor = db.cursor()

        # 🤖 ML PREDICTION
        vec = vectorizer.transform([url])
        prediction = model.predict(vec)[0]

        action = "allowed"
        reason = "Safe URL"

        if prediction == "malicious":
            action = "blocked"
            reason = "Detected by ML Model"

            # 🚨 Send Email
            send_email_alert(session["user"], url)

            # 🚫 DO NOT REDIRECT
            cursor.execute("""
                INSERT INTO weblogs
                (username, resource, type, action, reason, timestamp, whitelist, reviewed)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                session["user"],
                url,
                "URL",
                action,
                reason,
                datetime.now(),
                False,
                False
            ))

            db.commit()
            db.close()

            # STOP HERE — DO NOT OPEN WEBSITE
            return render_template("blocked.html", url=url, reason=reason)

        # ✅ SAFE URL
        cursor.execute("""
            INSERT INTO weblogs
            (username, resource, type, action, reason, timestamp, whitelist, reviewed)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            session["user"],
            url,
            "URL",
            action,
            reason,
            datetime.now(),
            False,
            True
        ))

        db.commit()
        db.close()

        return redirect(url)

    return render_template("scan_url.html")


# ================= FILE SCAN =================

@app.route("/file_scan", methods=["GET", "POST"])
def file_scan():
    if "user" not in session:
        return redirect("/login")

    if request.method == "POST":
        file = request.files["file"]
        filename = file.filename.lower()

        malicious_ext = [".exe", ".bat", ".cmd", ".scr"]

        if any(filename.endswith(ext) for ext in malicious_ext):
            action = "blocked"
            reason = "Suspicious file extension"
            send_email_alert(session["user"], filename)
        else:
            action = "allowed"
            reason = "Safe file"

        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO weblogs
            (username, resource, type, action, reason, timestamp, whitelist, reviewed)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            session["user"], filename, "FILE",
            action, reason, datetime.now(),
            False, False
        ))
        db.commit()
        db.close()

        return render_template("scan_file.html", result=reason)

    return render_template("scan_file.html")

# ================= ADMIN DASHBOARD =================

@app.route("/admin_dashboard")
def admin_dashboard():
    if "admin" not in session:
        return redirect("/admin/login")

    db = get_db()
    cursor = db.cursor()

    # Total scans
    cursor.execute("SELECT COUNT(*) FROM weblogs")
    total_scans = cursor.fetchone()[0]

    # Blocked URLs
    cursor.execute("SELECT COUNT(*) FROM weblogs WHERE action='blocked' AND type='URL'")
    blocked = cursor.fetchone()[0]

    # Malicious Files
    cursor.execute("SELECT COUNT(*) FROM weblogs WHERE action='blocked' AND type='FILE'")
    malicious_files = cursor.fetchone()[0]

    risk_score = round((blocked / total_scans) * 100, 2) if total_scans else 0
    safe_urls = total_scans - blocked
    db.close()

    return render_template(
    "admin_dashboard.html",
    total_scans=total_scans,
    blocked=blocked,
    malicious_files=malicious_files,
    risk_score=risk_score,
    safe_urls=safe_urls
)


# ================= ANALYTICS =================

@app.route("/admin/analytics")
def analytics():
    if "admin" not in session:
        return redirect("/admin/login")

    # ---- Load model metrics safely ----
    try:
        with open("model_metrics.json") as f:
            metrics = json.load(f)

        logistic_acc = metrics.get("Logistic Regression", {}).get("accuracy", 0)
        svm_acc = metrics.get("Linear SVM", {}).get("accuracy", 0)
        rf_acc = metrics.get("Random Forest", {}).get("accuracy", 0)

    except:
        logistic_acc = 0
        svm_acc = 0
        rf_acc = 0

    db = get_db()
    cursor = db.cursor()

    # Safe URLs
    cursor.execute("SELECT COUNT(*) FROM weblogs WHERE action='allowed'")
    safe_count = cursor.fetchone()[0] or 0

    # Malicious URLs
    cursor.execute("SELECT COUNT(*) FROM weblogs WHERE action='blocked'")
    malicious_count = cursor.fetchone()[0] or 0

    # Risk trend
    cursor.execute("""
        SELECT DATE(timestamp), COUNT(*)
        FROM weblogs
        WHERE action='blocked'
        GROUP BY DATE(timestamp)
    """)
    data = cursor.fetchall()
    db.close()

    dates = [str(row[0]) for row in data] if data else []
    risk_values = [row[1] for row in data] if data else []

    return render_template(
        "analytics.html",
        logistic_acc=float(logistic_acc),
        svm_acc=float(svm_acc),
        rf_acc=float(rf_acc),
        safe_count=int(safe_count),
        malicious_count=int(malicious_count),
        dates=dates,
        risk_values=risk_values
    )

# ================= ADMIN LOGIN =================

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        if request.form["username"] == "admin" and request.form["password"] == "admin":
            session["admin"] = True
            return redirect("/admin_dashboard")
        return render_template("admin_login.html", error="Invalid credentials")

    return render_template("admin_login.html")

# ================= ADMIN REVIEW =================

@app.route("/admin/review")
def review_logs():

    if "admin" not in session:
        return redirect("/admin/login")

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT id, username, resource, reason, timestamp
        FROM weblogs
        WHERE action='blocked' AND whitelist=FALSE
        ORDER BY timestamp DESC
    """)

    logs = cursor.fetchall()
    db.close()

    return render_template("admin_review.html", logs=logs)

# ================= UNBLOCK =================

@app.route("/admin/unblock/<int:log_id>")
def unblock_url(log_id):
    if "admin" not in session:
        return redirect("/admin/login")

    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT resource FROM weblogs WHERE id=%s", (log_id,))
    row = cursor.fetchone()

    if row:
        domain = row[0]

        # Remove from hosts file
        unblock_domain(domain)

        # Update ONLY this log entry
        cursor.execute("""
            UPDATE weblogs 
            SET action='allowed'
            WHERE id=%s
        """, (log_id,))

        db.commit()

    db.close()
    return redirect("/admin/review")


# ================= RUN =================

if __name__ == "__main__":
    app.run(debug=True)
