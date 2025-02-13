from transformers import BertTokenizer, BertForSequenceClassification, Trainer, TrainingArguments
from torch.utils.data import Dataset
import torch
import json

# Define the dataset class
class KeyQueryDataset(Dataset):
    def __init__(self, texts, labels, tokenizer, max_len):
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_len = max_len

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        text = self.texts[idx]
        label = self.labels[idx]
        encoding = self.tokenizer(
            text,
            max_length=self.max_len,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )
        return {
            'input_ids': encoding['input_ids'].squeeze(),
            'attention_mask': encoding['attention_mask'].squeeze(),
            'labels': torch.tensor(label, dtype=torch.long)
        }

# Example dataset
texts = [
    "Who is John's parent?",
    "What's the punishment for causing arson?",
    "Where is the Eiffel Tower located?",
    "Who is Mary's Mother?",
]
labels = [0, 1, 2, 3, 4, 5]  # Corresponding to key-query pairs
label_map = {0: 'key:John query:Parent', 1: 'key:Arson query:Punishment', 2: 'key:EiffelTower query:Location', 3: 'key:Mary query:Parent'}

# Save the label map to a file
with open('label_map.json', 'w') as f:
    json.dump(label_map, f)

# Load BERT tokenizer and model
tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
model = BertForSequenceClassification.from_pretrained('bert-base-uncased', num_labels=len(label_map))

# Move model to GPU if available
if torch.cuda.is_available():
    model.cuda()

# Prepare dataset
dataset = KeyQueryDataset(texts, labels, tokenizer, max_len=128)

# Training arguments
training_args = TrainingArguments(
    output_dir='./results',
    evaluation_strategy='epoch',
    learning_rate=2e-5,
    per_device_train_batch_size=8,
    per_device_eval_batch_size=8,
    num_train_epochs=100,  # Reduced number of epochs to prevent overfitting
    weight_decay=0.01,
    save_total_limit=1,
)

# Trainer
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=dataset,
    eval_dataset=dataset,
)

# Train the model
trainer.train()

# Save the model after fine-tuning
model.save_pretrained('./fine_tuned_bert')
tokenizer.save_pretrained('./fine_tuned_bert')

print("Model fine-tuned and saved successfully!")