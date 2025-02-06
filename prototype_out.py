from pyswip import prolog

import torch
from transformers import BartForConditionalGeneration, BartTokenizer

# Load the fine-tuned model and tokenizer
model = BartForConditionalGeneration.from_pretrained('./fine_tuned_bart')
tokenizer = BartTokenizer.from_pretrained('./fine_tuned_bart')

# Example usage: Generate Prolog code from English text
input_text = input()
inputs = tokenizer(input_text, return_tensors="pt", padding='max_length', truncation=True)
outputs = model.generate(**inputs)

# Decode the generated tokens to get the Prolog code
prolog_code = tokenizer.decode(outputs[0], skip_special_tokens=True)


# Initialize the Prolog engine
prolog = prolog.Prolog()
prolog.consult("Law.pro")
result = list(prolog.query(prolog_code))

if result:
    print(result[0]['Definition'])
else:
    print( "Definition not found.")
