from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import pickle
import numpy as np
import mysql.connector
from feature_extraction import extract_features
from tensorflow.keras.models import load_model

app = Flask(__name__)
app.secret_key = "supersecretkey"

# ----------------------------
# Load Models
# ----------------------------
rf_model = pickle.load(open("model/phishing_model.pkl", "rb"))
dl_model = load_model("model/deep_phishing_model.keras")   # ✅ FIX: changed .h5 → .keras

# Load saved accuracies
try:
    metrics_data = pickle.load(open("model/metrics.pkl", "rb"))
    rf_accuracy = metrics_data.get("rf_accuracy", 0)
    dl_accuracy = metrics_data.get("dl_accuracy", 0)
except:
    rf_accuracy = 0
    dl_accuracy = 0

# ----------------------------
# Admin Credentials
# ----------------------------
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

# ----------------------------
# Database Connection
# ----------------------------
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Chitty@6543",
        database="phishing_db"
    )

# ----------------------------
# Home  ✅ FIX: now calls real ML models instead of dummy "https" logic
# ----------------------------
@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        url = request.form.get('url')

        if not url:
            return render_template("index.html", prediction_text="Please enter a URL")

        try:
            # Feature extraction
            features = extract_features(url)
            final_features = np.array([features]).astype(float)

            # Random Forest Prediction
            rf_prediction = rf_model.predict(final_features)
            rf_prob = rf_model.predict_proba(final_features)
            rf_confidence = round(max(rf_prob[0]) * 100, 2)
            rf_result = "Phishing" if rf_prediction[0] == 1 else "Legitimate"

            # Deep Learning Prediction
            dl_prediction = dl_model.predict(final_features)
            dl_confidence = round(float(dl_prediction[0][0]) * 100, 2)
            dl_result = "Phishing" if dl_prediction[0][0] > 0.5 else "Legitimate"

            # Final combined result (majority vote)
            if rf_result == "Phishing" or dl_result == "Phishing":
                prediction_text = "⚠️ Phishing Website Detected!"
            else:
                prediction_text = "✅ Safe Website"

            avg_confidence = round((rf_confidence + dl_confidence) / 2, 2)

            # Save to Database
            db = get_db_connection()
            cursor = db.cursor()
            cursor.execute("""
                INSERT INTO predictions
                (url, rf_result, rf_confidence, dl_result, dl_confidence)
                VALUES (%s, %s, %s, %s, %s)
            """, (url, rf_result, rf_confidence, dl_result, dl_confidence))
            db.commit()
            cursor.close()
            db.close()

            return render_template(
                "index.html",
                prediction_text=prediction_text,
                confidence=avg_confidence,
                rf_result=rf_result,
                rf_confidence=rf_confidence,
                dl_result=dl_result,
                dl_confidence=dl_confidence
            )

        except Exception as e:
            print("Prediction Error:", e)
            return render_template("index.html", prediction_text=f"Error: {str(e)}")

    return render_template('index.html')

# ----------------------------
# Login
# ----------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['username'] == ADMIN_USERNAME and request.form['password'] == ADMIN_PASSWORD:
            session['admin'] = True
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error="Invalid Credentials")
    return render_template('login.html')

# ----------------------------
# Logout
# ----------------------------
@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect(url_for('login'))

# ----------------------------
# Dashboard
# ----------------------------
@app.route('/dashboard')
def dashboard():
    if 'admin' not in session:
        return redirect(url_for('login'))

    db = get_db_connection()
    cursor = db.cursor()

    cursor.execute("SELECT COUNT(*) FROM predictions")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM predictions WHERE rf_result='Phishing'")
    rf_phishing = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM predictions WHERE dl_result='Phishing'")
    dl_phishing = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM predictions WHERE rf_result != dl_result")
    disagreements = cursor.fetchone()[0]

    cursor.close()
    db.close()

    return render_template(
        "dashboard.html",
        total=total,
        rf_phishing=rf_phishing,
        dl_phishing=dl_phishing,
        disagreements=disagreements,
        rf_accuracy=rf_accuracy,
        dl_accuracy=dl_accuracy
    )

# ----------------------------
# History Page
# ----------------------------
@app.route('/history')
def history():
    if 'admin' not in session:
        return redirect(url_for('login'))

    db = get_db_connection()
    cursor = db.cursor()

    cursor.execute("""
        SELECT id, url, rf_result, rf_confidence,
               dl_result, dl_confidence, created_at
        FROM predictions
        ORDER BY id DESC
    """)

    records = cursor.fetchall()
    cursor.close()
    db.close()

    return render_template("history.html", records=records)

# ----------------------------
# Dashboard API
# ----------------------------
@app.route('/dashboard-data')
def dashboard_data():
    db = get_db_connection()
    cursor = db.cursor()

    cursor.execute("SELECT COUNT(*) FROM predictions")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM predictions WHERE rf_result='Phishing'")
    rf_phishing = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM predictions WHERE dl_result='Phishing'")
    dl_phishing = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM predictions WHERE rf_result != dl_result")
    disagreements = cursor.fetchone()[0]

    cursor.close()
    db.close()

    return jsonify({
        "total": total,
        "rf_phishing": rf_phishing,
        "dl_phishing": dl_phishing,
        "disagreements": disagreements
    })

# ----------------------------
# Run App
# ----------------------------
if __name__ == "__main__":
    app.run(debug=True)