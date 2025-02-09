import spacy
import openai
from pyswip import Prolog
import re

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

# Initialize Prolog
prolog = Prolog()
prolog.consult("Law.pro")  # Load your knowledge base

# OpenAI API Key (Replace with your actual API key)
openai.api_key = "your-api-key"

def ask_gpt(user_input):
    """Rewrites the user question into a structured legal query."""
    prompt = f"Rewrite this legal question in structured form for a database query: {user_input}"
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "system", "content": prompt}]
    )
    return response["choices"][0]["message"]["content"].strip()

def map_to_prolog_query(user_input):
    """Extracts keywords using NLP and maps them to Prolog queries."""
    doc = nlp(user_input.lower())
    
    # Extract entities
    entities = {ent.label_: ent.text for ent in doc.ents}
    
    # Define keyword patterns
    patterns = {
        "alien": re.compile(r"\balien\b"),
        "work": re.compile(r"\bwork\b"),
        "permit": re.compile(r"\bpermit\b"),
        "holder_of_permit": re.compile(r"\bholder of permit\b"),
        "employee": re.compile(r"\bemployee\b"),
        "fund": re.compile(r"\bfund\b"),
        "board": re.compile(r"\bboard\b"),
        "committee": re.compile(r"\bcommittee\b"),
        "appeal_committee": re.compile(r"\bappeal committee\b"),
        "execution_of_official": re.compile(r"\bexecution of official\b"),
        "registrar": re.compile(r"\bregistrar\b"),
        "director_general": re.compile(r"\bdirector general\b"),
        "minister": re.compile(r"\bminister\b")
    }
    
    # Match patterns
    for key, pattern in patterns.items():
        if pattern.search(user_input):
            return f"query_definition({key}, Result)"
    
    return "out of scope"

def chatbot():
    print("Legal Chatbot: Ask me about foreign worker laws in Thailand. Type 'exit' to quit.")

    while True:
        question = input("You: ").strip()

        if question.lower() in ["exit", "quit"]:
            print("Chatbot: Goodbye!")
            break

        # Use GPT to rephrase the question
        structured_question = ask_gpt(question)

        # Map to Prolog query
        query = map_to_prolog_query(structured_question)

        if query != "out of scope":
            results = list(prolog.query(query))
            if results:
                print("Chatbot:", results[0]['Result'])
            else:
                print("Chatbot: I don't have an answer for that.")
        else:
            print("Chatbot: I'm not sure, but I will try to improve!")

# Run chatbot
chatbot()