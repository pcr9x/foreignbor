import torch
from transformers import BartForConditionalGeneration, BartTokenizer, Trainer, TrainingArguments
from datasets import load_dataset

# Load the WikiAuto dataset with trust_remote_code=True
dataset = load_dataset("wiki_auto", trust_remote_code=True)

# Print the dataset structure to understand its keys
print(dataset)

# Load the BART model and tokenizer from Hugging Face
model_name = "facebook/bart-large"
model = BartForConditionalGeneration.from_pretrained(model_name)
tokenizer = BartTokenizer.from_pretrained(model_name)

# Tokenize the dataset
def tokenize_function(examples):
    # Flatten the list of sentences
    normal_articles = [" ".join(article['normal_article_content']['normal_sentence']) for article in examples['normal']]
    simple_articles = [" ".join(article['simple_article_content']['simple_sentence']) for article in examples['simple']]
    
    # Ensure the lengths match
    assert len(normal_articles) == len(simple_articles), "Mismatch in the number of normal and simple sentences"
    
    # Tokenize the sentences
    inputs = tokenizer(normal_articles, padding='max_length', truncation=True, max_length=512)
    targets = tokenizer(simple_articles, padding='max_length', truncation=True, max_length=512)
    inputs['labels'] = targets['input_ids']
    return inputs

tokenized_datasets = dataset.map(tokenize_function, batched=True, remove_columns=dataset['part_1'].column_names)

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
    save_steps=100,                  # Save checkpoint every 200 steps
    save_total_limit=3,              # Limit the total amount of checkpoints
    report_to="none",                # Disable reporting to avoid errors if no logging service is set up
)

# Initialize the Trainer
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_datasets['part_1'],
    eval_dataset=tokenized_datasets['part_2'],  # You can split the dataset into train and eval if needed
)

# Move model to GPU if available
if torch.cuda.is_available():
    model.to('cuda')

# Specify the path to the checkpoint directory
checkpoint_path = './results/checkpoint-600'  # Replace with the actual checkpoint path

# Fine-tune the model
trainer.train(resume_from_checkpoint=checkpoint_path)

# Save the model after fine-tuning
model.save_pretrained('./fine_tuned_bart')
tokenizer.save_pretrained('./fine_tuned_bart')

print("Model fine-tuned and saved successfully!")