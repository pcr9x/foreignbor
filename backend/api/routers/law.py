from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from ..database import supabase
from uuid import uuid4
from datetime import datetime

# Import the chatbot components
from pyswip import Prolog
from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline
from ollama import chat, ChatResponse
from sklearn.preprocessing import LabelEncoder
import json
import re

router = APIRouter()

# Initialize Prolog
prolog = Prolog()
prolog.consult("Law.pl")  # Load Prolog knowledge base

# Load Pretrained BERT Model for Intent Classification
INTENT_MODEL = "./results"
intent_tokenizer = AutoTokenizer.from_pretrained(INTENT_MODEL)
intent_model = AutoModelForSequenceClassification.from_pretrained(INTENT_MODEL)
intent_pipeline = pipeline(
    "text-classification", model=intent_model, tokenizer=intent_tokenizer, device=0
)

with open(f"{INTENT_MODEL}/IntentClassifierModel.json", "r") as f:
    label_classes = json.load(f)
label_encoder = LabelEncoder()
label_encoder.classes_ = label_classes

# Define intent mappings and required keys
INTENT_ENTITY_MAP = {
    "injury_case": [
        "PersonAge",
        "Injured",
        "Intent",
        "Grievous",
        "Prem",
        "Torture",
        "CrimeRelated",
        "VictimType",
        "ReasonableSelfDefense",
    ],
    "murder_case": [
        "PersonAge",
        "Intent",
        "Prem",
        "Torture",
        "CrimeRelated",
        "VictimType",
        "Death",
        "ReasonableSelfDefense",
    ],
    "negligent_case": ["PersonAge", "Grievous", "Death"],
    "suicide_cruelty_case": ["PersonAge", "Occurred", "Dependent", "UsedCruelty"],
    "suicide_aid_case": ["PersonAge", "Occurred", "SuicideVictimType"],
    "affray_case": ["PersonAge", "Death", "Prevented", "Grievous"],
}

# Define follow-up questions for missing keys (detailed)
FOLLOW_UP_QUESTIONS = {
    "PersonAge": "Is the person in question over 18 years old or not, as it can affect sentencing.",
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
    "ReasonableSelfDefense": "Did the accused act in self-defense when you used force to protect yourself 'in the heat of the moment,' such as by using an object as a weapon or stopping an intruder from escaping (e.g., tackling them)?",
    "Death": "Did the act result in the death of the victim? This directly influences whether the crime is classified as murder, attempted murder, or a lesser offense.",
    "Occurred": "Did the suicide actually occur or was it merely attempted? Both cases are considered serious, but the legal consequences may differ.",
    "Dependent": "Was the victim dependent on the accused for food, care, protection, or shelter? This includes minors, spouses, or people in the care of the offender.",
    "UsedCruelty": "Did the accused use any form of physical, emotional, or psychological cruelty toward the victim? This includes persistent abuse or threats.",
    "SuicideVictimType": (
        "How would you classify the person who attempted or committed suicide?\n"
        "- Child: Under 16 years old\n"
        "- Incompetent: Unable to understand the nature or seriousness of their actions\n"
        "- Uncontrollable: Lacking ability to control their own actions (e.g., due to mental state)\n"
        "- Other: Does not fit any of the above categories"
    ),
    "Prevented": "Did the accused attempt to stop or lawfully intervene in the situation (e.g., during a group fight)? If they took preventive actions, they may not be held responsible.",
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
    keys_with_context = {key: FOLLOW_UP_QUESTIONS[key] for key in required_keys}

    # Prepare the message content
    message_content = (
        f"Extract the required entities from the input below. "
        f"Respond in JSON format ONLY, with no explanation, put in null if no key is found for that category.\n\n"
        f"for yes/no questions, use 'yes' or 'no' as the answer.\n\n"
        f"for VictimType, use 'ascendant', 'official', 'official assistant' or 'other' as the answer, or null if not specified.\n\n"
        f"for SuicideVictimType, use 'child', 'incompetent', 'uncontrollable' or 'other' as the answer, or null if not specified.\n\n"
        f"Input: {user_input}\n"
        f"Keys and Context:\n{json.dumps(keys_with_context, indent=2)}\n\n"
        f"make sure the keys are in the same order as the input.\n\n"
    )

    # Call DeepSeek
    response: ChatResponse = chat(
        model="deepseek-r1:14b",
        messages=[{"role": "system", "content": message_content}],
    )

    try:
        # Extract only the JSON substring from the response
        json_match = re.search(r"\{.*?\}", response.message.content.strip(), re.DOTALL)
        if json_match:
            extracted_entities = json.loads(json_match.group(0))
            return extracted_entities
        else:
            return {}
    except json.JSONDecodeError:
        return {}


def query_from_prolog(prolog_query):
    """
    Queries the Prolog knowledge base with the constructed query.
    """
    try:
        result = list(prolog.query(prolog_query))
        return result
    except Exception as e:
        return []


class MessageInput(BaseModel):
    message: str
    id: str = None
    entities: Optional[Dict[str, Any]] = None


class ConversationState(BaseModel):
    intent: str
    required_keys: List[str]
    extracted_entities: Dict[str, Any]
    missing_keys: List[str]
    current_key_index: int = 0


# Create a new chat or continue an existing one
@router.post("/generate-answer")
async def generate_answer(msg: MessageInput):
    user_message = msg.message
    conversation_id = msg.id or str(uuid4())
    current_time = datetime.now().isoformat()

    # Check if there's an existing conversation state for this chat ID
    state_exists = False
    conversation_state = None

    if msg.id:
        try:
            state_response = (
                supabase.table("conversation_states")
                .select("state")
                .eq("chat_id", msg.id)
                .execute()
            )
            if state_response.data:
                state_exists = True
                conversation_state = state_response.data[0]["state"]
        except Exception:
            # If there's an error or the table doesn't exist, we'll create a new conversation
            pass

    # If this is a new conversation or we couldn't find an existing state
    if not state_exists:
        # Create a new chat entry if this is a new conversation
        if not msg.id:
            try:
                first_message = user_message if user_message else "Law Inquiry"
                summarized_title = first_message[:15]
                chat_response = (
                    supabase.table("chats")
                    .insert(
                        {
                            "id": conversation_id,
                            "title": summarized_title,
                            "last_updated": current_time,
                        }
                    )
                    .execute()
                )

                if not chat_response.data:
                    raise HTTPException(status_code=400, detail="Failed to create chat")
            except Exception as e:
                raise HTTPException(
                    status_code=400, detail=f"Error creating chat: {str(e)}"
                )

        # Step 1: Classify intent for new conversation
        intent = classify_intent(user_message)

        # Check if intent is supported
        if intent not in INTENT_ENTITY_MAP:
            answer = "Sorry, your case is out of scope. I can only help with injury cases, murder cases, negligent cases, suicide cases, and affray cases. Please provide details about one of these case types."

            # Store the user message and system response
            await store_messages(conversation_id, user_message, answer, current_time)

            return {"answer": answer, "conversationId": conversation_id}

        # Step 2: Get required keys for the intent
        required_keys = INTENT_ENTITY_MAP[intent]

        # Step 3: Extract entities
        extracted_entities = extract_entities(user_message, required_keys)

        # Step 4: Identify missing entities
        missing_keys = [
            key
            for key in required_keys
            if key not in extracted_entities or not extracted_entities[key]
        ]

        # Convert yes/no answers to true/false
        for key, value in extracted_entities.items():
            if value == "yes":
                extracted_entities[key] = "true"
            elif value == "no":
                extracted_entities[key] = "false"

        # Store conversation state in the database
        conversation_state = {
            "intent": intent,
            "required_keys": required_keys,
            "extracted_entities": extracted_entities,
            "missing_keys": missing_keys,
            "current_key_index": 0 if missing_keys else -1,
        }

        try:
            # Check if the conversation_states table exists
            try:
                supabase.table("conversation_states").select("*").limit(1).execute()
            except Exception:
                # If the table doesn't exist, create it
                supabase.query(
                    """
                    CREATE TABLE IF NOT EXISTS conversation_states (
                      id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                      chat_id UUID NOT NULL REFERENCES chats(id) ON DELETE CASCADE,
                      state JSONB NOT NULL,
                      created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                      updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    );
                    
                    CREATE INDEX IF NOT EXISTS idx_conversation_states_chat_id ON conversation_states(chat_id);
                """
                ).execute()

            # Insert the conversation state
            supabase.table("conversation_states").insert(
                {"chat_id": conversation_id, "state": conversation_state}
            ).execute()
        except Exception as e:
            # If there's an error storing the state, we'll continue without it
            pass

        # If no missing entities, generate the result
        if not missing_keys:
            # Process the complete case
            result = process_complete_case(intent, required_keys, extracted_entities)
            answer = format_result(result)

            # Store the user message and system response
            await store_messages(conversation_id, user_message, answer, current_time)

            return {"answer": answer, "conversationId": conversation_id}
        else:
            # Ask for the first missing entity
            current_key = missing_keys[0]
            answer = f"I need more information to assess your case. {FOLLOW_UP_QUESTIONS[current_key]}"

            # Store the user message and system response
            await store_messages(conversation_id, user_message, answer, current_time)

            return {"answer": answer, "conversationId": conversation_id}

    else:
        # This is a continuation of an existing conversation
        intent = conversation_state["intent"]
        required_keys = conversation_state["required_keys"]
        extracted_entities = conversation_state["extracted_entities"]
        missing_keys = conversation_state["missing_keys"]
        current_key_index = conversation_state["current_key_index"]

        # Process the user's response to the previous question
        if missing_keys and current_key_index < len(missing_keys):
            current_key = missing_keys[current_key_index]

            # Extract the answer for the specific key from the user's message
            if current_key == "VictimType":
                # Parse VictimType from user input
                user_answer = user_message.strip().lower()
                if "ascendant" in user_answer:
                    extracted_entities[current_key] = "ascendant"
                elif "official" in user_answer and "assistant" in user_answer:
                    extracted_entities[current_key] = "official assistant"
                elif "official" in user_answer:
                    extracted_entities[current_key] = "official"
                else:
                    extracted_entities[current_key] = "other"
            elif current_key == "SuicideVictimType":
                # Parse SuicideVictimType from user input
                user_answer = user_message.strip().lower()
                if "child" in user_answer:
                    extracted_entities[current_key] = "child"
                elif "incompetent" in user_answer:
                    extracted_entities[current_key] = "incompetent"
                elif "uncontrollable" in user_answer:
                    extracted_entities[current_key] = "uncontrollable"
                else:
                    extracted_entities[current_key] = "other"
            else:
                # Parse yes/no from user input
                user_answer = (
                    "yes"
                    if any(
                        word in user_message.lower()
                        for word in ["yes", "yeah", "yep", "correct", "true"]
                    )
                    else "no"
                )
                extracted_entities[current_key] = (
                    "true" if user_answer == "yes" else "false"
                )

            # Move to the next missing key
            current_key_index += 1

            # Update the conversation state
            conversation_state["extracted_entities"] = extracted_entities
            conversation_state["current_key_index"] = current_key_index

            try:
                supabase.table("conversation_states").update(
                    {"state": conversation_state}
                ).eq("chat_id", conversation_id).execute()
            except Exception:
                # If there's an error updating the state, we'll continue
                pass

            # Check if we need more information
            if current_key_index < len(missing_keys):
                # Ask for the next missing entity
                next_key = missing_keys[current_key_index]
                answer = FOLLOW_UP_QUESTIONS[next_key]

                # Store the user message and system response
                await store_messages(
                    conversation_id, user_message, answer, current_time
                )

                return {"answer": answer, "conversationId": conversation_id}
            else:
                # We have all the information needed, process the case
                result = process_complete_case(
                    intent, required_keys, extracted_entities
                )
                answer = format_result(result)

                # Store the user message and system response
                await store_messages(
                    conversation_id, user_message, answer, current_time
                )

                return {"answer": answer, "conversationId": conversation_id}
        else:
            # We already have all the information, process the case again
            result = process_complete_case(intent, required_keys, extracted_entities)
            answer = format_result(result)

            # Store the user message and system response
            await store_messages(conversation_id, user_message, answer, current_time)

            return {"answer": answer, "conversationId": conversation_id}


def process_complete_case(intent, required_keys, extracted_entities):
    """Process a case where all required entities are provided."""
    # Construct Prolog query
    prolog_args = [str(extracted_entities[key]) for key in required_keys]
    prolog_query = f"clear_case, handle_case({intent}(person, victim, {', '.join(prolog_args)})), sentence(person, S)."

    # Query Prolog and get results
    result = query_from_prolog(prolog_query)

    return {
        "intent": intent,
        "entities": extracted_entities,
        "result": result if result else None,
    }


def format_result(result_data):
    """Format the legal result into a human-readable response."""
    if not result_data["result"]:
        return "Based on the information provided, I couldn't determine a clear legal outcome. This might require more detailed analysis by a legal professional."

    # Format the Prolog result
    response = "Based on my analysis of Thai criminal law:\n\n"

    # Add case type
    intent_display = {
        "injury_case": "Injury Case",
        "murder_case": "Murder Case",
        "negligent_case": "Negligent Injury/Death Case",
        "suicide_cruelty_case": "Suicide Due to Cruelty Case",
        "suicide_aid_case": "Suicide Assistance Case",
        "affray_case": "Affray (Fighting) Case",
    }

    response += f"Case Type: {intent_display.get(result_data['intent'], result_data['intent'])}\n\n"

    # Add the sentence information
    for res in result_data["result"]:
        if "S" in res:
            sentence = res["S"]
            # Check if the sentence is a byte string and decode it
            if isinstance(sentence, bytes):
                sentence = sentence.decode("utf-8")
            response += f"Potential Sentence: {sentence}\n\n"

    response += "Note: This is a preliminary assessment based on Thai criminal law. For a definitive legal opinion, please consult with a qualified legal professional in Thailand."

    return response


async def store_messages(conversation_id, user_message, system_response, timestamp):
    """Store user message and system response in the database."""
    try:
        # Store user message
        user_message_response = (
            supabase.table("chat_messages")
            .insert(
                {
                    "message": user_message,
                    "sender": "user",
                    "chat_id": conversation_id,
                    "timestamp": timestamp,
                }
            )
            .execute()
        )

        if not user_message_response.data:
            raise HTTPException(status_code=400, detail="Failed to store user message")

        # Store system response
        system_response_data = (
            supabase.table("chat_messages")
            .insert(
                {
                    "message": system_response,
                    "sender": "system",
                    "chat_id": conversation_id,
                    "timestamp": timestamp,
                }
            )
            .execute()
        )

        if not system_response_data.data:
            raise HTTPException(
                status_code=400, detail="Failed to store system message"
            )

        # Update the chat's last_updated timestamp
        supabase.table("chats").update({"last_updated": timestamp}).eq(
            "id", conversation_id
        ).execute()

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error storing messages: {str(e)}")


@router.get("/chats")
async def get_chats():
    try:
        # Fetch chats ordered by last_updated
        chats_response = (
            supabase.table("chats")
            .select("*")
            .order("last_updated", desc=True)
            .execute()
        )

        return {"chats": chats_response.data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error fetching chats: {str(e)}")


@router.get("/chat/{chat_id}")
async def get_chat(chat_id: str):
    try:
        # Fetch chat messages for the given chat_id
        chat_messages_response = (
            supabase.table("chat_messages")
            .select("*")
            .eq("chat_id", chat_id)
            .order("timestamp", desc=False)
            .execute()
        )

        return {"messages": chat_messages_response.data}
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Error fetching chat messages: {str(e)}"
        )


@router.delete("/chat/{chat_id}")
async def delete_chat(chat_id: str):
    try:
        # Try to delete the conversation state first (if exists)
        try:
            supabase.table("conversation_states").delete().eq(
                "chat_id", chat_id
            ).execute()
        except Exception:
            # If the table doesn't exist or there's an error, continue
            pass

        # Delete chat and its messages
        supabase.table("chats").delete().eq("id", chat_id).execute()

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error deleting chat: {str(e)}")

    return {"message": "Chat deleted successfully"}
