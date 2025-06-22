import os
import json
import spacy
import random
import requests
import datetime
from dotenv import load_dotenv
from spacy.matcher import Matcher, PhraseMatcher

# Load environment variables from .env ofc!!
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")


nlp = spacy.load("en_core_web_sm")

# loading faqs.json
with open("faqs.json", "r") as f:
    faq_data = json.load(f)

# Setting up matchers
matcher = Matcher(nlp.vocab)
phrase_matcher = PhraseMatcher(nlp.vocab, attr="LOWER")

# Keyword-based patterns
matcher.add("WEATHER", [[{"LOWER": "weather"}]])
matcher.add("JOKE", [[{"LOWER": "joke"}]])
matcher.add("PYTHON", [[{"LOWER": "python"}]])

# Phrase-based patterns
phrases = ["tell me a joke", "explain python", "how's the weather", "python programming"]
phrase_patterns = [nlp(text) for text in phrases]
phrase_matcher.add("CUSTOM_PHRASES", None, *phrase_patterns)

# NLP categories (Basic wla)
GREETINGS = ["hi", "hello", "hey", "greetings"]
FAREWELLS = ["bye", "goodbye", "see you"]
THANKS = ["thanks", "thank"]
SAD_WORDS = ["sad", "depressed", "unhappy", "tired"]
HAPPY_WORDS = ["happy", "excited", "joyful", "great"]

advanced_mode = False



def detect_intent(doc):
    lemmas = [token.lemma_.lower() for token in doc]
    if any(word in lemmas for word in GREETINGS):
        return "greeting"
    elif any(word in lemmas for word in FAREWELLS):
        return "farewell"
    elif any(word in lemmas for word in THANKS):
        return "thanks"
    elif any(word in lemmas for word in SAD_WORDS):
        return "sad"
    elif any(word in lemmas for word in HAPPY_WORDS):
        return "happy"
    return "unknown"


def detect_name(doc):
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            return ent.text
    return None


def handle_basic_questions(user_input):
    text = user_input.lower()
    if "your name" in text:
        return "I'm your terminal chatbot!"
    if "time" in text:
        return f"The current time is {datetime.datetime.now().strftime('%H:%M:%S')}."
    if "date" in text:
        return f"Today's date is {datetime.date.today().strftime('%Y-%m-%d')}."
    return None

# JOKE_LIST
joke_l = ["Why don't scientists trust atoms? Because they make up everything!",
        "What do you get if you cross a cat with a dark horse? Kitty Perry.",
        "Parallel lines have so much in common… it’s a shame they’ll never meet.",
        "C and C++ went to a five star bar, C was stopped by the gate guards because C got no class.",
        "Why do programmers prefer dark mode? Because light attracts bugs!",
        "Why do Python programmers prefer using snakes? Because they can’t handle the exceptions!",
        "Why do programmers hate nature? It has too many bugs.",
        "Why do Java developers wear glasses? Because they don't see sharp!",
        "Why did the programmer quit his job? Because he didn't get arrays!",
        "I was about to crack a joke on Ubuntu’s text editor, but you might not gedit.",
        "Two bytes meet. The first byte asks, “Are you ill?” The second byte replies, “No, just feeling a bit off.”",
        "The XML processor was having a rough day. His friend came by and gave him some words of encouragement — “This too shall parse”.",
        "“Knock knock!” “Who is there?” “Yah!” “Yah, who?” “No not Yahoo, Google.”",
        "All programmers are playwrights, and all computers are lousy actors."]

# Rule-based response 
def rule_based_response(user_input):
    doc = nlp(user_input)

    # Phrase matching
    phrase_matches = phrase_matcher(doc)
    if phrase_matches:
        for match_id, start, end in phrase_matches:
            span = doc[start:end].text.lower()
            if "joke" in span:
                return random.choice(joke_l)
            elif "python" in span:
                return "Python is a high-level programming language known for its simplicity and power."
            elif "weather" in span:
                return "I can't fetch live weather data offline, but it's always sunny inside the terminal!"

    # Keyword matching
    matches = matcher(doc)
    for match_id, start, end in matches:
        match_name = nlp.vocab.strings[match_id]
        if match_name == "WEATHER":
            return "I can't check the weather offline, but you can try /mode advanced!"
        elif match_name == "JOKE":
            return random.choice(joke_l)
        elif match_name == "PYTHON":
            return "Python is great for web, AI, data science, and everything in between!"

    # Name detection
    name = detect_name(doc)
    if name:
        return f"Nice to meet you, {name}!"

    # Basic time/date
    basic = handle_basic_questions(user_input)
    if basic:
        return basic

    # FAQ
    for question, answer in faq_data.items():
        if question.lower() in user_input.lower():
            return answer

    # Emotion/greeting intent
    intent = detect_intent(doc)
    if intent == "greeting":
        return random.choice(["Hi there!", "Hello!", "Hey!"])
    elif intent == "farewell":
        return random.choice(["Goodbye!", "Take care!", "See you!"])
    elif intent == "thanks":
        return "You're welcome!"
    elif intent == "sad":
        return "I'm here for you. Things will get better!"
    elif intent == "happy":
        return "That's awesome to hear! 😊"

    return None


# Gemini API integration
def ask_gemini_api(query):
    if not GOOGLE_API_KEY:
        return "⚠️ Gemini not available. Set GOOGLE_API_KEY."

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GOOGLE_API_KEY}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": query}]}]
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        data = response.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        return f"⚠️ Error calling Gemini: {str(e)}"


# Help text
def show_help():
    return """
📘 Commands:
/help - Show available commands
/faq - Show available FAQ questions
/mode advanced - Enable Gemini-powered AI mode (requires internet)
/mode basic - Use offline rule-based NLP mode
/exit - Exit the chatbot

💡 Tip: In advanced mode, you can ask *anything*!
"""

def show_faq():
    if not faq_data:
        return "📭 No FAQs available."
    result = "📚 Frequently Asked Questions:\n"
    for q in faq_data:
        result += f"• {q.capitalize()}\n"
    return result

# Main chatbot (loop)
def chatbot():
    global advanced_mode
    print("🤖 Chatbot ready! Type /help for commands.")

    while True:
        user_input = input("You: ").strip()
        if not user_input:
            continue

        # Handle commands
        if user_input.lower() == "/help":
            print(show_help())
            continue
        elif user_input.lower() == "/faq":
            print(show_faq())
            continue
        elif user_input.lower() == "/exit":
            print("👋 Goodbye!")
            break
        elif user_input.lower() == "/mode advanced":
            if GOOGLE_API_KEY:
                advanced_mode = True
                print("✅ Advanced AI mode (Gemini) enabled.")
            else:
                print("⚠️ Gemini not available. Set GOOGLE_API_KEY.")
            continue
        elif user_input.lower() == "/mode basic":
            advanced_mode = False
            print("🔄 Switched to basic offline mode.")
            continue

        # Respond
        if not advanced_mode:
            response = rule_based_response(user_input)
            if response:
                print("Bot:", response)
            else:
                print("🤔 I don't know the answer. Try /mode advanced for smarter answers.")
        else:
            response = ask_gemini_api(user_input)
            print("Bot:", response)


if __name__ == "__main__":
    chatbot()