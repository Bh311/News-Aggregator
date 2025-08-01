# emotion_model.py

import joblib

# Load the full pipeline: vectorizer + classifier
model = joblib.load("emotion_detection/emotion_classifier_pipe_lr.pkl")

def predict_emotion(text):
    """Returns the predicted emotion for a given text."""
    return model.predict([text])[0]
