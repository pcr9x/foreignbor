from pyswip import Prolog
from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline
from ollama import chat, ChatResponse
from sklearn.preprocessing import LabelEncoder
import json
import re

# Initialize Prolog
prolog = Prolog()
prolog.consult("Law.pl")  # Load Prolog knowledge base

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
    "injury_case" : ["PersonAge", "Injured", "Intent", "Grievous"," Prem", "Torture", "CrimeRelated", "VictimType"],
    "murder_case" : ["PersonAge", "Intent"," Prem", "Torture", "CrimeRelated", "VictimType", "Death"],
    "negligent_case" : ["PersonAge", "Circumstance", "Grievous", "Death"],
    "suicide_cruelty_case" : ["PersonAge", "VictimAge", "Occurred", "Dependent", "UsedCruelty"],
    "suicide_aid_case" : ["PersonAge", "VictimAge", "Occurred", "VictimType"],
    "affray_case" : ["PersonAge", "Death", "Prevented", "Grievous"]
}

# Define follow-up questions for missing keys (detailed)
FOLLOW_UP_QUESTIONS = {
    "PersonAge": "What is the age of the person who committed the act? Are they over 18?",
    "Injured": "Was the victim physically or mentally injured as a result of the act?",
    "Intent": "Was the act committed intentionally or accidentally?",
    "Grievous":
        """Did the victim suffer grievous bodily harm? Grievous injuries include:\n
        1. Loss of sight, hearing, tongue, or sense of smell\n
        2. Loss of reproductive organs or ability\n
        3. Loss of limbs, fingers, or other body parts\n
        4. Permanent disfiguration of the face\n
        5. Abortion caused by the act\n
        6. Permanent mental illness or insanity\n
        7. Chronic illness or severe pain lasting over 20 days\n
        8. Inability to perform ordinary duties for over 20 days""",
    "Prem": "Was the act committed after premeditation or planning?",
    "Torture": "Did the person use torture or acts of cruelty while committing the act?",
    "CrimeRelated": "Was the act done to commit, conceal, benefit from, or escape punishment for another crime?",
    "VictimType": 
        """What is the relationship or status of the victim? Choose from:\n
        - Ascendant (e.g. parent or grandparent)\n
        - Official (e.g. police, judge, etc. in duty)\n
        - Assistant to an official\n
        - Other (no special status)""",
    "Death": "Did the victim die as a result of the act?",
    "Circumstance": "What was the negligent or careless circumstance that led to the incident?",
    "Occurred": "Was the suicide attempt successful, or did the person survive?",
    "VictimAge": "How old was the victim at the time of the incident?",
    "Dependent": "Was the victim dependent on the accused for care, support, or living needs?",
    "UsedCruelty": "Did the accused use cruel behavior, threats, or abuse toward the victim?",
    "Prevented": "Did the person try to prevent the fight or act in lawful self-defense?"
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
        f"for yes/no questions, use 'yes' or 'no' as the answer.\n\n"
        f"for VictimType, use 'ascendant', 'official', 'official assistant' or 'other' as the answer.\n\n"
        f"Input: {user_input}\n"
        f"Keys and Context:\n{json.dumps(keys_with_context, indent=2)}\n\n"
        f"make sure the keys are in the same order as the input.\n\n"
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
    Iteratively asks the user for missing entities with yes/no questions or specific options.
    """
    for key in required_keys:
        if key not in extracted_entities or not extracted_entities[key]:
            # Ask the user for the missing entity
            if key == "VictimType":
                print(FOLLOW_UP_QUESTIONS[key])
                while True:
                    user_response = input("> ").strip().lower()
                    if user_response in ["ascendant", "official", "official assistant", "other"]:
                        extracted_entities[key] = user_response
                        break
                    else:
                        print("Please choose from: ascendant, official, official assistant, or other.")
            else:
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
    if intent not in INTENT_ENTITY_MAP:
        print("out of scope.")
        exit(1)
    
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
    prolog_query = f"handle_case({intent}(Person, Victim, {', '.join(prolog_args)}))."
    print(f"Prolog Query: {prolog_query}")
    
#    clear_case,
#    handle_case(injury_case(ella, frank, 40, true, true, true, true, true, false, official)),
#    sentence(ella, S).