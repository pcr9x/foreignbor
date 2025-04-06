from pyswip import Prolog
from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline
from ollama import chat, ChatResponse
from sklearn.preprocessing import LabelEncoder
import json
import re

# Initialize Prolog
prolog = Prolog()
prolog.consult("Law.pro")  # Load Prolog knowledge base

# Load Pretrained BERT Model for Intent Classification
INTENT_MODEL = "./results"
intent_tokenizer = AutoTokenizer.from_pretrained(INTENT_MODEL)
intent_model = AutoModelForSequenceClassification.from_pretrained(INTENT_MODEL)
intent_pipeline = pipeline("text-classification", model=intent_model, tokenizer=intent_tokenizer, device=0)

with open(f"{INTENT_MODEL}/IntentClassifierModel.json", "r") as f:
    label_classes = json.load(f)
label_encoder = LabelEncoder()
label_encoder.classes_ = label_classes

# Define intent mappings and required keys
INTENT_ENTITY_MAP = {
    "murder": ["intentional", "self-defense", "special_victim"],
    "theft": ["item_stolen", "value", "location"],
    # Add more legal classifications and their required keys here
}

# Define follow-up questions for missing keys
FOLLOW_UP_QUESTIONS = {
    "intentional": "Was the act intentional?",
    "self-defense": "Was it self-defense?",
    "special_victim": "Was the victim a government official?",
    "item_stolen": "What item was stolen?",
    "value": "What was the value of the stolen item?",
    "location": "Where did the theft occur?",
    # Add more follow-up questions for other keys here
}

def classify_intent(user_input):
    """Predicts intent using the BERT classification model."""
    result = intent_pipeline(user_input)[0]
    label_map = {f"LABEL_{i}": label for i, label in enumerate(label_encoder.classes_)}
    return label_map[result["label"]]


def extract_entities(user_input, required_keys):
    """
    Extracts required entities from user input using the DeepSeek library.
    """
    print(f"Extracting entities for keys: {required_keys}")
    keys_with_context = {key: FOLLOW_UP_QUESTIONS[key] for key in required_keys}

    # Prepare the message content
    message_content = (
        f"Extract the required entities from the input below. "
        f"Respond in JSON format ONLY, with no explanation, put in null if no key is found for that category.\n\n"
        f"Input: {user_input}\n"
        f"Keys and Context:\n{json.dumps(keys_with_context, indent=2)}\n\n"
        f"Example output:\n"
        f'{{ "intentional": "yes", "self-defense": "no", "special_victim": null }}'
    )

    # Print the message content for debugging
    print("Message sent to DeepSeek:")
    #print(message_content)

    # Call DeepSeek
    response: ChatResponse = chat(
        model="deepseek-r1:14b",
        messages=[
            {
                "role": "system",
                "content": message_content
            }
        ],
    )
    
    try:
        # Extract only the JSON substring from the response
        print(response.message.content.strip())
        json_match = re.search(r"\{.*?\}", response.message.content.strip(), re.DOTALL)
        if json_match:
            print("Extracted JSON:")
            extracted_entities = json.loads(json_match.group(0))
            return extracted_entities
        else:
            print("Error: No JSON found in DeepSeek response.")
            return {}
    except json.JSONDecodeError:
        print("Error: DeepSeek returned invalid JSON.")
        return {}

def ask_for_missing_entities_yes_no(extracted_entities, required_keys):
    """
    Iteratively asks the user for missing entities with yes/no questions.
    """
    for key in required_keys:
        if key not in extracted_entities or not extracted_entities[key]:
            # Ask the user for the missing entity
            print(FOLLOW_UP_QUESTIONS[key])
            while True:
                user_response = input("> ").strip().lower()
                if user_response in ["yes", "no"]:
                    # Map "yes" to the key name and "no" to "_"
                    extracted_entities[key] = key if user_response == "yes" else "_"
                    break
                else:
                    print("Please answer with 'yes' or 'no'.")
        elif extracted_entities[key] == "yes":
            extracted_entities[key] = key
        elif extracted_entities[key] == "no":
            extracted_entities[key] = "_"
    return extracted_entities

# Example usage
if __name__ == "__main__":
    user_input = input("Enter your legal query: ").strip()
    
    # Step 1: Classify intent
    intent = classify_intent(user_input)
    print(f"Classified Intent: {intent}")
    
    # Step 2: Get required keys for the classified intent
    required_keys = INTENT_ENTITY_MAP.get(intent, [])
    
    # Step 3: Extract entities using deepseek
    extracted_entities = {}
    if required_keys:
        extracted_entities = extract_entities(user_input, required_keys)
        print(f"Extracted Entities: {extracted_entities}")
    # Step 4: Ask for missing entities with yes/no questions
    extracted_entities = ask_for_missing_entities_yes_no(extracted_entities, required_keys)
    
    # Step 5: Construct Prolog query
    prolog_args = [extracted_entities[key] for key in required_keys]
    prolog_query = f"{intent}({', '.join(prolog_args)}, Punishment)."
    print(f"Prolog Query: {prolog_query}")