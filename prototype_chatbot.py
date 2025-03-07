from transformers import AutoModelForSequenceClassification, AutoModelForTokenClassification, AutoTokenizer, pipeline
from sklearn.preprocessing import LabelEncoder
import json

# Load Pretrained Models
INTENT_MODEL = "./results"  
NER_MODEL = "dbmdz/bert-large-cased-finetuned-conll03-english"

# Load the label encoder
with open(f"{INTENT_MODEL}/label_encoder.json", "r") as f:
    label_classes = json.load(f)
label_encoder = LabelEncoder()
label_encoder.classes_ = label_classes

# Tokenizers, models, and pipelines for Intent Classification 
intent_tokenizer = AutoTokenizer.from_pretrained(INTENT_MODEL)
intent_model = AutoModelForSequenceClassification.from_pretrained(INTENT_MODEL)
intent_pipeline = pipeline("text-classification", model=intent_model, tokenizer=intent_tokenizer, device=0)  # Use GPU for inference

# Tokenizers, models, and pipelines for Named Entity Recognition
ner_tokenizer = AutoTokenizer.from_pretrained(NER_MODEL)
ner_model = AutoModelForTokenClassification.from_pretrained(NER_MODEL)
ner_pipeline = pipeline("ner", model=ner_model, tokenizer=ner_tokenizer, device=0)  # Use GPU for inference

# Define intents and required entities
INTENT_ENTITY_MAP = {
    "employment_rights": ["country"],
    "termination_policy": ["contract_type", "notice_period"],
    "work_hours": ["country"],
    "littering_penalty": ["country"]
}

def classify_intent(user_input):
    """Classify the user's intent."""
    result = intent_pipeline(user_input)[0]
    label_map = {f"LABEL_{i}": label for i, label in enumerate(label_encoder.classes_)}
    return label_map[result["label"]]  # Map the predicted label to the original label

def extract_entities(user_input):
    """Extract entities from the user's query."""
    entities = ner_pipeline(user_input)
    extracted = {e["entity"]: e["word"] for e in entities}
    return extracted

def check_missing_entities(intent, extracted_entities):
    """Check if any required entities are missing."""
    required_entities = set(INTENT_ENTITY_MAP.get(intent, []))
    found_entities = set(extracted_entities.keys())

    missing = required_entities - found_entities
    return list(missing)

def process_user_input(user_input):
    """Process the input, predict intent, extract entities, and handle missing info."""
    intent = classify_intent(user_input)
    entities = extract_entities(user_input)
    
    missing_entities = check_missing_entities(intent, entities)
    
    if missing_entities:
        return f"Missing details: {missing_entities}. Could you provide more information?"
    
    return f"Intent: {intent}\nExtracted Entities: {entities}"

# Example
user_input = "What is the minimum wage?"
response = process_user_input(user_input)
print(response)