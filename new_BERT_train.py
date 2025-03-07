import json
import torch
import pandas as pd
from transformers import AutoTokenizer, AutoModelForSequenceClassification, TrainingArguments, Trainer, pipeline
from datasets import Dataset, load_dataset
from sklearn.preprocessing import LabelEncoder

class IntentClassifier:
    def __init__(self, model_name="bert-base-uncased", dataset_path="dataset.json", output_dir="./results"):
        self.model_name = model_name
        self.dataset_path = dataset_path
        self.output_dir = output_dir
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.label_encoder = LabelEncoder()
        self.model = None
        self.trainer = None
    
    def get_texts(self):
        with open("dataset.json", "r") as f:
            raw_data = json.load(f)["data"]
        texts = [item["text"] for item in raw_data]
        return texts

    def load_dataset(self):
        with open(self.dataset_path, "r") as f:
            raw_data = json.load(f)["data"]
        df = pd.DataFrame(raw_data)
        df.to_json("intent_dataset.jsonl", orient="records", lines=True)
        dataset = load_dataset("json", data_files="intent_dataset.jsonl")
        return dataset

    def tokenize_function(self, examples):
        return self.tokenizer(examples["text"], padding="max_length", truncation=True)

    def prepare_data(self, dataset):
        tokenized_datasets = dataset.map(self.tokenize_function, batched=True)
        encoded_labels = self.label_encoder.fit_transform(dataset["train"]["intent"])
        tokenized_datasets["train"] = tokenized_datasets["train"].add_column("labels", encoded_labels)
        return tokenized_datasets

    def initialize_model(self, num_labels):
        self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name, num_labels=num_labels)

    def train_model(self, tokenized_datasets):
        training_args = TrainingArguments(
            output_dir=self.output_dir,
            evaluation_strategy="no",
            save_strategy="no",
            per_device_train_batch_size=8,
            num_train_epochs=100,
            weight_decay=0.01,
            logging_dir='./logs',
            logging_steps=10,
            fp16=True,  # Enable mixed precision training
        )
        self.trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=tokenized_datasets["train"],
        )
        self.trainer.train()

    def save_model(self):
        self.trainer.save_model(self.output_dir)
        self.tokenizer.save_pretrained(self.output_dir)
        with open(f"{self.output_dir}/label_encoder.json", "w") as f:
            json.dump(self.label_encoder.classes_.tolist(), f)

    def load_model_for_inference(self):
        return pipeline("text-classification", model=self.output_dir, tokenizer=self.tokenizer, device=0)  # Use GPU for inference

    def predict_intent(self, text, classifier):
        prediction = classifier(text)
        label_map = {f"LABEL_{i}": label for i, label in enumerate(self.label_encoder.classes_)}
        predicted_label = label_map[prediction[0]["label"]]
        return predicted_label

if __name__ == "__main__":
    classifier = IntentClassifier()
    dataset = classifier.load_dataset()
    tokenized_datasets = classifier.prepare_data(dataset)
    classifier.initialize_model(num_labels=len(classifier.label_encoder.classes_))
    classifier.train_model(tokenized_datasets)
    classifier.save_model()

    # Load model for inference
    inference_classifier = classifier.load_model_for_inference()


    trained_texts = classifier.get_texts()
    for sample_text in trained_texts:
        predicted_intent = classifier.predict_intent(sample_text, inference_classifier)
        print(f"Predicted intent for '{sample_text}': {predicted_intent}")
