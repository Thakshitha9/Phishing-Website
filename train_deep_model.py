import pandas as pd
import numpy as np
import pickle
from feature_extraction import extract_features
from sklearn.model_selection import train_test_split
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense

# Load dataset
df = pd.read_csv("dataset/custom_urls.csv")

# Remove accidental duplicate header rows (if any)
df = df[df["label"] != "label"]

# Convert label column to integer
df["label"] = df["label"].astype(int)

# Extract features
X = []
for url in df["url"]:
    X.append(extract_features(url))

# Convert to numpy arrays
X = np.array(X).astype(float)
y = df["label"].values

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Build neural network
model = Sequential()
model.add(Dense(16, input_dim=X.shape[1], activation='relu'))
model.add(Dense(8, activation='relu'))
model.add(Dense(1, activation='sigmoid'))

model.compile(loss='binary_crossentropy',
              optimizer='adam',
              metrics=['accuracy'])

# Train
model.fit(X_train, y_train, epochs=50, batch_size=8, verbose=1)

# Evaluate
loss, accuracy = model.evaluate(X_test, y_test)
dl_accuracy = round(accuracy * 100, 2)
print("Deep Learning Accuracy:", dl_accuracy, "%")

# ✅ FIX: Save model as .keras (consistent with app.py)
model.save("model/deep_phishing_model.keras")
print("Deep learning model saved as deep_phishing_model.keras")

# ✅ FIX: Save accuracy to metrics.pkl so dashboard can display it
try:
    metrics_data = pickle.load(open("model/metrics.pkl", "rb"))
except:
    metrics_data = {}

metrics_data["dl_accuracy"] = dl_accuracy
pickle.dump(metrics_data, open("model/metrics.pkl", "wb"))
print("DL accuracy saved to metrics.pkl:", dl_accuracy, "%")