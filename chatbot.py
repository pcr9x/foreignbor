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
    "injury_case" : ["PersonAge", "Injured", "Intent", "Grievous","Prem", "Torture", "CrimeRelated", "VictimType"],
    "murder_case" : ["PersonAge", "Intent"," Prem", "Torture", "CrimeRelated", "VictimType", "Death"],
    "negligent_case" : ["PersonAge", "Circumstance", "Grievous", "Death"],
    "suicide_cruelty_case" : ["PersonAge", "VictimAge", "Occurred", "Dependent", "UsedCruelty"],
    "suicide_aid_case" : ["PersonAge", "VictimAge", "Occurred", "SuicideVictimType"],
    "affray_case" : ["PersonAge", "Death", "Prevented", "Grievous"]
}

# Define follow-up questions for missing keys (detailed)
FOLLOW_UP_QUESTIONS = {
    "PersonAge": "What is the age of the person who committed the act? Please confirm whether they are over 18 years old or not, as it can affect sentencing.",
    
    "Injured": "Was the victim physically or mentally injured as a result of the act? Even minor harm may count in legal terms.",
    
    "Intent": "Was the act committed intentionally, or was it an accident? Intent is important for determining the severity of punishment.",
    
    "Grievous": (
        "Did the victim suffer grievous bodily harm? This includes any of the following:\n"
        "1. Loss of senses such as sight, hearing, speech, or smell\n"
        "2. Loss of reproductive organs or function\n"
        "3. Loss of limbs or major body parts (e.g., hand, foot, finger)\n"
        "4. Permanent disfigurement of the face\n"
        "5. Forced abortion\n"
        "6. Permanent insanity\n"
        "7. Chronic illness or pain lasting 20+ days, or inability to follow daily activities for the same period"
    ),
    
    "Prem": "Was the act premeditated or planned in advance? Premeditation increases the severity of criminal liability.",
    
    "Torture": "Was any form of torture or excessive cruelty used in the commission of the act? This can lead to aggravated sentencing.",
    
    "CrimeRelated": (
        "Was this act committed to support, conceal, or escape punishment from another crime? For example:\n"
        "- To silence a witness\n"
        "- To destroy evidence\n"
        "- To help commit another offense"
    ),
    
    "VictimType": (
        "What is the classification of the victim? Choose from the following types:\n"
        "- Ascendant: A parent, grandparent, or ancestor\n"
        "- Official: A government officer performing their duty\n"
        "- Assistant: A person aiding an official\n"
        "- Other: None of the above"
    ),
    
    "Death": "Did the act result in the death of the victim? This directly influences whether the crime is classified as murder, attempted murder, or a lesser offense.",
    
    "Occurred": "Did the suicide actually occur or was it merely attempted? Both cases are considered serious, but the legal consequences may differ.",
    
    "Dependent": "Was the victim dependent on the accused for food, care, protection, or shelter? This includes minors, spouses, or people in the care of the offender.",
    
    "UsedCruelty": "Did the person use any form of physical, emotional, or psychological cruelty toward the victim? This includes persistent abuse or threats.",
    
    "SuicideVictimType": (
        "How would you classify the person who attempted or committed suicide?\n"
        "- Child: Under 16 years old\n"
        "- Incompetent: Unable to understand the nature or seriousness of their actions\n"
        "- Uncontrollable: Lacking ability to control their own actions (e.g., due to mental state)\n"
        "- Other: Does not fit any of the above categories"
    ),
    
    "Prevented": "Did the accused attempt to stop or lawfully intervene in the situation (e.g., during a group fight)? If they took preventive actions, they may not be held responsible."
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
            elif key == "SuicideVictimType":
                print(FOLLOW_UP_QUESTIONS[key])
                while True:
                    user_response = input("> ").strip().lower()
                    if user_response in ["child", "incompetent", "uncontrollable"]:
                        extracted_entities[key] = user_response
                        break
                    else:
                        print("Please choose from: child, incompetent, or uncontrollable.")
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