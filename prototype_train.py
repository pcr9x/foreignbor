import torch
from transformers import BartForConditionalGeneration, BartTokenizer, Trainer, TrainingArguments
from datasets import Dataset
import json

# Load your English-Prolog pairs in JSON format
data = json.load(open("prototype.json", "r"))

# Convert the data to a Hugging Face dataset
dataset = Dataset.from_dict({
    'input_text': [item['english'] for item in data],
    'target_text': [item['prolog'] for item in data]
})

# Load the BART model and tokenizer from Hugging Face
model_name = "facebook/bart-large"  # You can use other BART variants as well
model = BartForConditionalGeneration.from_pretrained(model_name)
tokenizer = BartTokenizer.from_pretrained(model_name)

# Tokenize the dataset
def tokenize_function(examples):
    return tokenizer(examples['input_text'], padding='max_length', truncation=True)

tokenized_datasets = dataset.map(tokenize_function, batched=True)

# Prepare the inputs and labels
def preprocess_data(examples):
    inputs = tokenizer(examples['input_text'], padding='max_length', truncation=True)
    targets = tokenizer(examples['target_text'], padding='max_length', truncation=True)
    inputs['labels'] = targets['input_ids']
    return inputs

tokenized_datasets = tokenized_datasets.map(preprocess_data, batched=True)

# Define training arguments
training_args = TrainingArguments(
    output_dir='./results',          # Output directory for the model and logs
    evaluation_strategy="epoch",     # Evaluation during training
    learning_rate=5e-5,              # Learning rate
    per_device_train_batch_size=4,   # Batch size per device during training
    per_device_eval_batch_size=4,    # Batch size per device during evaluation
    num_train_epochs=3,              # Number of training epochs
    weight_decay=0.01,               # Weight decay for optimization
    logging_dir='./logs',            # Directory for logs
    logging_steps=10,
)

# Initialize the Trainer
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_datasets,
    eval_dataset=tokenized_datasets,  # You can split the dataset into train and eval if needed
)

# Fine-tune the model
trainer.train()

# Save the model after fine-tuning
model.save_pretrained('./fine_tuned_bart')
tokenizer.save_pretrained('./fine_tuned_bart')

print("Model fine-tuned and saved successfully!")


