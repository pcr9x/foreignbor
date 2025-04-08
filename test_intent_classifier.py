from BERT_train import IntentClassifier
import json
import torch
import pandas as pd
from transformers import AutoTokenizer, AutoModelForSequenceClassification, TrainingArguments, Trainer, pipeline
from datasets import Dataset, load_dataset
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import KFold
from sklearn.metrics import precision_score, recall_score, f1_score, accuracy_score
from transformers import EarlyStoppingCallback

classifier = IntentClassifier()
dataset = classifier.load_dataset()

# Encode labels
classifier.label_encoder.fit([item["intent"] for item in dataset])  # Fit the label encoder

# Load model for inference
inference_classifier = classifier.load_model_for_inference()

trained_texts = ["What will happens if I injured someone accidentally",]
for sample_text in trained_texts:
    predicted_intent, confidence = classifier.predict_intent(sample_text, inference_classifier)
    print(f"Predicted intent for '{sample_text}': {predicted_intent} , Confidence: {confidence:.2f}")
