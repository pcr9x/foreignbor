import json
import torch
import pandas as pd
from transformers import AutoTokenizer, AutoModelForSequenceClassification, TrainingArguments, Trainer, pipeline
from datasets import Dataset, load_dataset
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import KFold
from sklearn.metrics import precision_score, recall_score, f1_score, accuracy_score
from transformers import EarlyStoppingCallback

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
        with open(self.dataset_path, "r") as f:
            raw_data = json.load(f)["data"]
        texts = [item["text"] for item in raw_data]
        return texts

    def load_dataset(self):
        with open(self.dataset_path, "r") as f:
            raw_data = json.load(f)["data"]  # No "train" key
        return raw_data  # Return the raw data directly as a list of dictionaries

    def tokenize_function(self, examples):
        return self.tokenizer(examples["text"], padding="max_length", truncation=True)

    def initialize_model(self, num_labels):
        self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name, num_labels=num_labels)

        
    def train_model(self, train_dataset, eval_dataset=None):
        training_args = TrainingArguments(
            output_dir=self.output_dir,
            evaluation_strategy="epoch" if eval_dataset else "no",  # Evaluate at the end of each epoch
            save_strategy="no",
            #save_strategy="epoch",  
            #save_total_limit=1,  
            load_best_model_at_end=False,  # Load the best model based on the evaluation metric
            metric_for_best_model="eval_accuracy",  # Use accuracy as the metric to monitor
            greater_is_better=True,  # Higher accuracy is better
            per_device_train_batch_size=8,
            num_train_epochs=20,  # Set a high number of epochs; early stopping will stop training earlier
            weight_decay=0.01,
            learning_rate=5e-5,
            logging_dir='./logs',
            logging_steps=10,
            fp16=True,  # Enable mixed precision training
        )
        self.trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=eval_dataset,
            compute_metrics=self.compute_metrics,
            #callbacks=[EarlyStoppingCallback(early_stopping_patience=3)],  # Early stopping after 3 evaluations without improvement
        )

        self.trainer.train()
        self.trainer.save_model(self.output_dir)  # Save the model
        self.tokenizer.save_pretrained(self.output_dir)  # Save the tokenizer
        with open(f"{self.output_dir}/IntentClassifierModel.json", "w") as f:
            json.dump(self.label_encoder.classes_.tolist(), f)  # Save the label encoder

    def compute_metrics(self, p):
        preds = p.predictions.argmax(-1)
        precision = precision_score(p.label_ids, preds, average="weighted")
        recall = recall_score(p.label_ids, preds, average="weighted")
        f1 = f1_score(p.label_ids, preds, average="weighted")
        accuracy = accuracy_score(p.label_ids, preds)
        return {"accuracy": accuracy, "precision": precision, "recall": recall, "f1": f1}

    def load_model_for_inference(self):
        return pipeline("text-classification", model=self.output_dir, tokenizer=self.tokenizer, device=0)  # Use GPU for inference

    def predict_intent(self, text, classifier):
        prediction = classifier(text)
        label_map = {f"LABEL_{i}": label for i, label in enumerate(self.label_encoder.classes_)}
        predicted_label = label_map[prediction[0]["label"]]
        return predicted_label

    def KF_cross_validate(self, dataset, n_splits=5):
        kf = KFold(n_splits=n_splits, shuffle=True, random_state=42)
        texts = [item["text"] for item in dataset]
        intents = [item["intent"] for item in dataset]
        
        # Fit the LabelEncoder once on the entire dataset
        self.label_encoder.fit(intents)
        results = []

        for fold, (train_index, val_index) in enumerate(kf.split(texts)):
            print(f"Starting fold {fold + 1}/{n_splits}...")

            # Split the dataset into training and validation sets
            train_texts = [texts[i] for i in train_index]
            val_texts = [texts[i] for i in val_index]
            train_intents = [intents[i] for i in train_index]
            val_intents = [intents[i] for i in val_index]

            # Create datasets for this fold
            train_dataset = Dataset.from_dict({"text": train_texts, "intent": train_intents})
            val_dataset = Dataset.from_dict({"text": val_texts, "intent": val_intents})

            # Tokenize the datasets
            tokenized_train = train_dataset.map(self.tokenize_function, batched=True)
            tokenized_val = val_dataset.map(self.tokenize_function, batched=True)

            # Add labels to the tokenized datasets
            tokenized_train = tokenized_train.add_column("labels", self.label_encoder.transform(train_intents))
            tokenized_val = tokenized_val.add_column("labels", self.label_encoder.transform(val_intents))

            # Initialize and train the model for this fold
            self.initialize_model(num_labels=len(self.label_encoder.classes_))
            self.train_model(tokenized_train, tokenized_val)

            # Evaluate the model on the validation set
            eval_result = self.trainer.evaluate(eval_dataset=tokenized_val)
            print(f"Fold {fold + 1} Accuracy: {eval_result['eval_accuracy']}")
            results.append(eval_result["eval_accuracy"])

        # Calculate and return the average accuracy across all folds
        avg_accuracy = sum(results) / len(results)
        print(f"Average Accuracy across {n_splits} folds: {avg_accuracy}")
        return avg_accuracy

    def LOO_cross_validate(self, dataset):
        texts = [item["text"] for item in dataset]
        intents = [item["intent"] for item in dataset]
        
        # Fit the LabelEncoder once on the entire dataset
        self.label_encoder.fit(intents)
        results = []

        for i in range(len(texts)):
            print(f"Starting iteration {i + 1}/{len(texts)}...")

            # Leave one out: Use one sample as validation and the rest as training
            train_texts = texts[:i] + texts[i+1:]
            val_texts = [texts[i]]
            train_intents = intents[:i] + intents[i+1:]
            val_intents = [intents[i]]

            # Create datasets for this iteration
            train_dataset = Dataset.from_dict({"text": train_texts, "intent": train_intents})
            val_dataset = Dataset.from_dict({"text": val_texts, "intent": val_intents})

            # Tokenize the datasets
            tokenized_train = train_dataset.map(self.tokenize_function, batched=True)
            tokenized_val = val_dataset.map(self.tokenize_function, batched=True)

            # Add labels to the tokenized datasets
            tokenized_train = tokenized_train.add_column("labels", self.label_encoder.transform(train_intents))
            tokenized_val = tokenized_val.add_column("labels", self.label_encoder.transform(val_intents))

            # Initialize and train the model for this iteration
            self.initialize_model(num_labels=len(self.label_encoder.classes_))
            self.train_model(tokenized_train, tokenized_val)

            # Evaluate the model on the validation set
            eval_result = self.trainer.evaluate(eval_dataset=tokenized_val)
            print(f"Iteration {i + 1} Accuracy: {eval_result['eval_accuracy']}")
            results.append(eval_result["eval_accuracy"])

        # Calculate and return the average accuracy across all iterations
        avg_accuracy = sum(results) / len(results)
        print(f"Average Accuracy across {len(texts)} iterations: {avg_accuracy}")
        return avg_accuracy
    
if __name__ == "__main__":
    classifier = IntentClassifier()
    dataset = classifier.load_dataset()  # Load the dataset directly

    # Encode labels
    classifier.label_encoder.fit([item["intent"] for item in dataset])  # Fit the label encoder

    # Perform K-Fold cross-validation
    avg_accuracy = classifier.KF_cross_validate(dataset)
    print(f"Final Average Accuracy: {avg_accuracy}")

    # Load model for inference
    inference_classifier = classifier.load_model_for_inference()

    trained_texts = classifier.get_texts()
    for sample_text in trained_texts:
        predicted_intent = classifier.predict_intent(sample_text, inference_classifier)
        print(f"Predicted intent for '{sample_text}': {predicted_intent}")

