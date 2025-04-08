import json
import torch
import pandas as pd
from transformers import AutoTokenizer, AutoModelForSequenceClassification, TrainingArguments, Trainer, pipeline
from datasets import Dataset, load_dataset
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import KFold, train_test_split
from sklearn.metrics import precision_score, recall_score, f1_score, accuracy_score, confusion_matrix, classification_report
from transformers import EarlyStoppingCallback
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

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
            eval_strategy="epoch" if eval_dataset else "no",  # Evaluate at the end of each epoch
            save_strategy="epoch",  
            save_total_limit=1,  
            load_best_model_at_end=True,  # Load the best model based on the evaluation metric
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
            callbacks=[EarlyStoppingCallback(early_stopping_patience=3)],  # Early stopping after 3 evaluations without improvement
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
    
    
    def KF_cross_validate(self, dataset, n_splits=5):
        # Perform 80:20 train-test split
        texts = [item["text"] for item in dataset]
        intents = [item["intent"] for item in dataset]
        train_texts, test_texts, train_intents, test_intents = train_test_split(
            texts, intents, test_size=0.2, random_state=42, stratify=intents
        )

        # Fit the LabelEncoder on the training set
        self.label_encoder.fit(train_intents)

        # Create the test dataset (this will not be part of K-Fold)
        test_dataset = Dataset.from_dict({"text": test_texts, "intent": test_intents})
        tokenized_test = test_dataset.map(self.tokenize_function, batched=True)
        tokenized_test = tokenized_test.add_column("labels", self.label_encoder.transform(test_intents))

        # Perform K-Fold cross-validation on the training set
        kf = KFold(n_splits=n_splits, shuffle=True, random_state=42)
        fold_results = []
        test_results = []
     
        
        for fold, (train_index, val_index) in enumerate(kf.split(train_texts)):
            print(f"Starting fold {fold + 1}/{n_splits}...")
               

            # Split the training set into K-Fold training and validation sets
            fold_train_texts = [train_texts[i] for i in train_index]
            fold_val_texts = [train_texts[i] for i in val_index]
            fold_train_intents = [train_intents[i] for i in train_index]
            fold_val_intents = [train_intents[i] for i in val_index]

            # Create datasets for this fold
            fold_train_dataset = Dataset.from_dict({"text": fold_train_texts, "intent": fold_train_intents})
            fold_val_dataset = Dataset.from_dict({"text": fold_val_texts, "intent": fold_val_intents})

            # Tokenize the datasets
            tokenized_train = fold_train_dataset.map(self.tokenize_function, batched=True)
            tokenized_val = fold_val_dataset.map(self.tokenize_function, batched=True)

            # Add labels to the tokenized datasets
            tokenized_train = tokenized_train.add_column("labels", self.label_encoder.transform(fold_train_intents))
            tokenized_val = tokenized_val.add_column("labels", self.label_encoder.transform(fold_val_intents))

            # Initialize and train the model for this fold
            self.initialize_model(num_labels=len(self.label_encoder.classes_))
            self.train_model(tokenized_train, tokenized_val)

            # Evaluate the model on the validation set
            val_result = self.trainer.evaluate(eval_dataset=tokenized_val)
            print(f"Fold {fold + 1} Validation Accuracy: {val_result['eval_accuracy']}")
            fold_results.append(val_result["eval_accuracy"])

            # Generate predictions and confusion matrix for the validation set
            val_predictions = np.argmax(self.trainer.predict(tokenized_val).predictions, axis=1)
            val_true_labels = tokenized_val["labels"]
            val_conf_matrix = confusion_matrix(val_true_labels, val_predictions)

            # Plot confusion matrix for validation set
            self.plot_confusion_matrix(val_conf_matrix, self.label_encoder.classes_, f"Fold {fold + 1} Validation Set")

            # Evaluate the model on the test set
            test_result = self.trainer.evaluate(eval_dataset=tokenized_test)
            print(f"Fold {fold + 1} Test Set Accuracy: {test_result['eval_accuracy']}")
            test_results.append(test_result["eval_accuracy"])

            # Generate predictions and confusion matrix for the test set
            test_predictions = np.argmax(self.trainer.predict(tokenized_test).predictions, axis=1)
            test_true_labels = tokenized_test["labels"]
            test_conf_matrix = confusion_matrix(test_true_labels, test_predictions)

            # Plot confusion matrix for test set
            self.plot_confusion_matrix(test_conf_matrix, self.label_encoder.classes_, f"Fold {fold + 1} Test Set")

        # Calculate and return the average accuracy across all folds and the test set
        avg_fold_accuracy = sum(fold_results) / len(fold_results)
        avg_test_accuracy = sum(test_results) / len(test_results)
        print(f"Average Validation Accuracy across {n_splits} folds: {avg_fold_accuracy}")
        print(f"Average Test Set Accuracy across {n_splits} folds: {avg_test_accuracy}")

        return avg_fold_accuracy, avg_test_accuracy

    def plot_confusion_matrix(self, conf_matrix, class_names, title):
        """
        Plots a confusion matrix using Seaborn heatmap.
        """
        plt.figure(figsize=(10, 8))
        sns.heatmap(conf_matrix, annot=True, fmt="d", cmap="Blues", xticklabels=class_names, yticklabels=class_names)
        plt.title(title)
        plt.xlabel("Predicted Labels")
        plt.ylabel("True Labels")
        plt.tight_layout()
        plt.show()
    
    def load_model_for_inference(self):
        return pipeline("text-classification", model=self.output_dir, tokenizer=self.tokenizer, device=0)  # Use GPU for inference

    def predict_intent(self, text, classifier):
        prediction = classifier(text)
        label_map = {f"LABEL_{i}": label for i, label in enumerate(self.label_encoder.classes_)}
        predicted_label = label_map[prediction[0]["label"]]
        confidence = prediction[0]["score"]
        if confidence < 0.7:
            return "Out of scope", confidence
        return predicted_label, confidence

   

   
    
if __name__ == "__main__":
    classifier = IntentClassifier()
    dataset = classifier.load_dataset()  # Load the dataset directly

    # Encode labels
    classifier.label_encoder.fit([item["intent"] for item in dataset])  # Fit the label encoder

    # Perform K-Fold cross-validation
    avg_accuracy, actual_accruacy   = classifier.KF_cross_validate(dataset)
    print(f"Final Average Accuracy: {avg_accuracy}")
    print(f"Final Test Set actual Accuracy: {actual_accruacy}")

    # Load model for inference
    inference_classifier = classifier.load_model_for_inference()

    trained_texts = classifier.get_texts()
    for sample_text in trained_texts:
        predicted_intent, confidence = classifier.predict_intent(sample_text, inference_classifier)
        print(f"Predicted intent for '{sample_text}': {predicted_intent}, Confidence: {confidence}")

