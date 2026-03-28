import pandas as pd
import pickle
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from feature_extraction import extract_features

# Load custom dataset
df = pd.read_csv("dataset/custom_urls.csv")

# Extract features
X = []
for url in df["url"]:
    X.append(extract_features(url))

y = df["label"]

# Train test split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Train model
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Evaluate
y_pred = model.predict(X_test)
rf_accuracy = round(accuracy_score(y_test, y_pred) * 100, 2)
print("Model Accuracy:", rf_accuracy, "%")

# Save model
pickle.dump(model, open("model/phishing_model.pkl", "wb"))
print("Random Forest model saved!")

# ✅ FIX: Save accuracy to metrics.pkl so dashboard can display it
try:
    metrics_data = pickle.load(open("model/metrics.pkl", "rb"))
except:
    metrics_data = {}

metrics_data["rf_accuracy"] = rf_accuracy
pickle.dump(metrics_data, open("model/metrics.pkl", "wb"))
print("RF accuracy saved to metrics.pkl:", rf_accuracy, "%")