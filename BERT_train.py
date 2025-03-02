from transformers import BertTokenizer, BertForSequenceClassification, Trainer, TrainingArguments
from torch.utils.data import Dataset
import torch
import json

#Dataset class
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


# Datasets
texts = [
    #0
    "what is alien",
    "what does alien mean",
    "what is the definition of the word alien",
    "define alien",
    "explain alien",
    #1
    "what is work",
    "what does work mean",
    "what does working mean",
    "what is the definition of work",
    "define work",
    "explain work",
    #2
    "what is permit",
    "what does permit mean",
    "what is the definition of permit",
    "define permit",
    "explain permit",
    #3
    "who is the holder of permit",
    "define holder of permit",
    "explain holder of permit",
    "who is permit holder"
    #4
    "what is an employee",
    "define employee",
    "explain employee",
    "who is an employee",
    #5
    "what is the fund",
    "define fund",
    "explain fund",
    #6
    "what is the board",
    "define board",
    "explain board",
    #7
    "what is the committee",
    "define committee",
    "explain committee",
    #8
    "what is the appeal committee",
    "define appeal committee",
    "explain appeal committee",
    #9
    "who is the execution of official",
    "define execution of official",
    "explain execution of official",
    #10
    "who is the registrar",
    "define registrar",
    "explain registrar",
    #11
    "who is the director general",
    "define director general",
    "explain director general",
    #12
    "who is the minister",
    "define minister",
    "explain minister"
    #13
    "what work can aliens do?",
    "what is the regualtions for the works aliens can do?",
    "what is the work that aliens can do?",
    "what is section 7 of the act?",
    "what work can standards aliens do?",
    #14
    "what is the reason for section 8?",
    "why do i have to pay hiring levy",
    "what is the hiring levy for?",
    "why do i have to pay extra to hire alien workers?",
    #15
    "what is section 8 of the act?",
    "do I have to pay levy when hiring alien workers?",
    "what does section 8 of the act say?",
    "what is the levy for hiring alien workers?",
    "when do i have to pay levy for hiring alien workers?",
    "do i have to pay anything when hiring alien workers?",
    
    #16
    "what is the penalty for not paying the levy?",
    "what will happen if i don't pay the levy",
    "what is the punishment for not paying the levy?",
    "what if i cannot pay levy on time?",
    "what is the penalty for not paying the levy on time?",
]

labels = [
    0, 0, 0, 0, 0,  # alien
    1, 1, 1, 1, 1, 1,  # work
    2, 2, 2, 2, 2,   # permit
    3, 3, 3, 3,        # holder_of_permit
    4, 4, 4, 4,       # employee
    5, 5, 5,        # fund
    6, 6, 6,        # board
    7, 7, 7,        # committee
    8, 8, 8,        # appeal_committee
    9, 9, 9,        # execution_of_official
    10, 10, 10,     # registrar
    11, 11, 11,     # director_general
    12, 12, 12,     # minister
    13, 13, 13, 13, 13,     # workable_work
    14, 14, 14, 14,      # reason_sec8
    15, 15, 15, 15, 15, 15,     # sec8
    16, 16, 16, 16, 16,  # sec8_penalty
]

label_map = {
    0: 'query_definition(alien, Result).',
    1: 'query_definition(work, Result).',
    2: 'query_definition(permit, Result).',
    3: 'query_definition(holder_of_permit, Result).',
    4: 'query_definition(employee, Result).',
    5: 'query_definition(fund, Result).',
    6: 'query_definition(board, Result).',
    7: 'query_definition(committee, Result).',
    8: 'query_definition(appeal_committee, Result).',
    9: 'query_definition(execution_of_official, Result).',
    10: 'query_definition(registrar, Result).',
    11: 'query_definition(director_general, Result).',
    12: 'query_definition(minister, Result).',
    13: 'sec7(Result).',
    14: 'reason_sec8(Result).',
    15: 'sec8(Result).',
    16: 'sec8_penalty(standards, Result).',
}

# Save the label map to a file
with open('label_map.json', 'w') as f:
    json.dump(label_map, f)

# Load BERT tokenizer and model
tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
model = BertForSequenceClassification.from_pretrained('bert-base-uncased', num_labels=len(label_map))

#use GPU to train if available
if torch.cuda.is_available():
    model.cuda()

# Prepare dataset
dataset = KeyQueryDataset(texts, labels, tokenizer, max_len=128)

# Training args
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

# Fine-tune the model
trainer.train()

# Save the model
model.save_pretrained('./fine_tuned_bert')
tokenizer.save_pretrained('./fine_tuned_bert')

print("Model fine-tuned and saved successfully!")