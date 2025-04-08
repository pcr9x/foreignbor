from ollama import chat
from ollama import ChatResponse
from chatbot import FOLLOW_UP_QUESTIONS
from chatbot import extract_entities

userinput = "john punched a guy in a bar 2 days ago what will happen to him"
required_keys = ["PersonAge", "Injured", "Intent", "Grievous","Prem", "Torture", "CrimeRelated", "VictimType"]


extracted_entities = extract_entities(userinput, required_keys)
print(extracted_entities)

userinput = "My friend bullied a kid in school and he shot himself. what will happen to him?"
required_keys = ["PersonAge", "VictimAge", "Occurred", "SuicideVictimType"]

extracted_entities = extract_entities(userinput, required_keys)
print(extracted_entities)