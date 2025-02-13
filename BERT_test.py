import json
from transformers import BertTokenizer, BertForSequenceClassification
import torch

# Load the trained BERT tokenizer and model
tokenizer = BertTokenizer.from_pretrained('./fine_tuned_bert')
model = BertForSequenceClassification.from_pretrained('./fine_tuned_bert')

# Move model to GPU if available
if torch.cuda.is_available():
    model.cuda()

# Load the label map from the file
with open('label_map.json', 'r') as f:
    label_map = json.load(f)

# Inference function
def classify_sentence(sentence):
    encoding = tokenizer(sentence, return_tensors='pt', padding=True, truncation=True, max_length=128)
    if torch.cuda.is_available():
        encoding = {key: value.cuda() for key, value in encoding.items()}
    outputs = model(**encoding)
    logits = outputs.logits
    predicted_class = torch.argmax(logits, dim=1).item()
    return label_map[str(predicted_class)]

print('-----------Test from traning data-----------')
print(classify_sentence("Who is John's parent?"))  # Output: key:John query:Parent
print(classify_sentence("What's the punishment for causing arson?"))  # Output: key:Arson query:Punishment
print(classify_sentence("Where is the Eiffel Tower located?"))  # Output: key:EiffelTower query:Location
print(classify_sentence("Who is Mary's Mother?"))  # Output: key:Mary query:Parent

print('-----------Test from new data-----------')
print(classify_sentence("Where can I find the Eiffel tower??"))  # Output: key:EiffelTower query:Location
print(classify_sentence("What is the penalty for causing arson?"))  # Output: key:Arson query:Punishment
print(classify_sentence("Who is the father of John?"))  # Output: key:John query:Parent
print(classify_sentence("Who is Mary's Gaurdian?"))  # Output: key:Mary query:Parent


