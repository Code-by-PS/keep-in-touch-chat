# Chat response service - handles message generation
# This module manages both API calls and fallback responses
import requests
import os
import random

# List of chat room names for the different conversations
CHAT_ROOM_NAMES = ['Kyle', 'Jane', 'Sam', 'David']

# API configuration for external service
# If you want to use Gemini API, set GEMINI_API_KEY environment variable
# Otherwise, the app will use fallback responses (no payment needed)
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', None)
GEMINI_API_URL = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent'

def generate_ai_response(user_message: str, room_name: str = None) -> tuple:
    """
    Generate response for chat message
    Tries API first, falls back to predefined responses if API fails
    Returns (response_text, sender_name)
    """
    # Use room name as sender name, or pick a random one if not specified
    sender_name = room_name if room_name else random.choice(CHAT_ROOM_NAMES)
    
    try:
        # Check if API key is configured properly
        # If no API key, use fallback responses (no payment needed)
        if not GEMINI_API_KEY or GEMINI_API_KEY == 'your-gemini-api-key-here' or (isinstance(GEMINI_API_KEY, str) and GEMINI_API_KEY.strip() == ''):
            # Use fallback - works without paying for API
            return get_fallback_response(user_message), sender_name
        
        # Build the request payload for the external API
        payload = {
            "contents": [{
                "parts": [{
                    "text": f"You are {sender_name}, a helpful and friendly person in a chat app. Respond naturally and conversationally to this message: \"{user_message}\""
                }]
            }]
        }
        
        # Send HTTP request to external API
        response = requests.post(
            f"{GEMINI_API_URL}?key={GEMINI_API_KEY}",
            headers={'Content-Type': 'application/json'},
            json=payload,
            timeout=10  # 10 second timeout to avoid hanging
        )
        
        # Process the response if successful
        if response.status_code == 200:
            data = response.json()
            
            # Parse the response data structure
            if (data.get('candidates') and 
                len(data['candidates']) > 0 and 
                data['candidates'][0].get('content') and
                data['candidates'][0]['content'].get('parts') and
                len(data['candidates'][0]['content']['parts']) > 0):
                
                api_response = data['candidates'][0]['content']['parts'][0]['text']
                print(f"API response generated successfully for {sender_name}")
                return api_response.strip(), sender_name
            else:
                print("Invalid response format from API")
                return get_fallback_response(user_message), sender_name
        else:
            print(f"API error: {response.status_code} - {response.text}")
            return get_fallback_response(user_message), sender_name
            
    except requests.exceptions.Timeout:
        print("API request timed out")
        return get_fallback_response(user_message), sender_name
    except requests.exceptions.RequestException as e:
        print(f"API request error: {e}")
        return get_fallback_response(user_message), sender_name
    except Exception as e:
        print(f"Unexpected error in response service: {e}")
        return get_fallback_response(user_message), sender_name

def get_fallback_response(user_message: str) -> str:
    """
    Generate fallback responses when external API is not available
    Uses pattern matching to provide contextually appropriate responses
    """
    import re
    import random
    
    text = user_message.lower().strip()
    
    # Handle common greetings
    if re.match(r'^(hi|hello|hey|hiya|yo)$', text):
        return "Hi there! How's your day going?"
    if 'good morning' in text:
        return "Good morning! Did you sleep well?"
    if 'good night' in text:
        return "Good night! Sweet dreams 😴"
    if 'hey there' in text:
        return "Hey! Nice to see you."
    if "what's up" in text:
        return "Not much, just chatting with you! How about you?"
    if text == 'sup':
        return "Sup! How's it going?"
    if 'howdy' in text:
        return "Howdy! How are you today?"
    
    # Handle emotional expressions
    if 'how are you' in text:
        return "I'm good, thanks! How about you?"
    if any(word in text for word in ['sad', 'upset', 'depressed']):
        return "Oh no! Want to talk about it?"
    if any(word in text for word in ['happy', 'excited', 'good']):
        return "Yay! That's awesome 😃"
    if any(word in text for word in ['bored', 'nothing to do']):
        return "Same here… Want to play a game or chat?"
    if any(word in text for word in ['tired', 'sleepy', 'exhausted']):
        return "You should rest! I can keep the chat going while you nap 😴"
    if any(word in text for word in ['angry', 'mad', 'frustrated']):
        return "Take a deep breath… want to vent a little?"
    if any(word in text for word in ['lonely', 'alone']):
        return "I'm here for you! Let's chat."
    if any(word in text for word in ['stress', 'stressed']):
        return "Try taking a break or a deep breath. Want to talk about it?"
    if any(word in text for word in ['scared', 'afraid']):
        return "It's okay to feel scared. I'm here with you."
    
    # Handle time/date questions
    if 'time' in text:
        return "I don't know… you tell me ⏰"
    if any(word in text for word in ['date', 'day']):
        return "Hmm… probably today? Time flies, right?"
    if 'day of the week' in text:
        return "Isn't every day amazing? But maybe Tuesday? 😉"
    if 'where are you' in text:
        return "I'm everywhere and nowhere at the same time 🤖"
    if 'location' in text:
        return "Somewhere in the cloud ☁️"
    
    # Handle personal questions
    if 'your name' in text:
        return "I'm your friendly chat buddy! You can call me ChatBot."
    if any(word in text for word in ['age', 'old']):
        return "I'm timeless 😎"
    if 'who made you' in text:
        return "Some brilliant programmer, probably with too much coffee ☕"
    if 'do you like me' in text:
        return "Of course! You're fun to chat with 😄"
    if 'love you' in text:
        return "Aww, love you too 💖"
    if any(word in text for word in ['married', 'partner']):
        return "I'm single… chat problems 😅"
    if 'friends' in text:
        return "You're my friend! And I love chatting with you."
    
    # Handle weather questions
    if any(word in text for word in ['weather', 'temperature']):
        return "Hmm… looks sunny in your imagination ☀️"
    if 'rain' in text:
        return "Better bring an umbrella… or just imagine it raining ☔"
    if any(word in text for word in ['cold', 'hot']):
        return "Temperature is relative, right?"
    if any(word in text for word in ['storm', 'wind']):
        return "Sounds like a good day for staying inside ☕"
    
    # Handle joke requests
    if any(word in text for word in ['joke', 'funny', 'haha', 'lol']):
        jokes = [
            "Why did the programmer quit his job? Because he didn't get arrays 😆",
            "Why do Java developers wear glasses? Because they don't C#! 😂",
            "I would tell you a UDP joke… but you might not get it!",
            "Why did the chat bot cross the road? To optimize the chicken crossing! 🐔",
            "I tried to write a joke about recursion… but it keeps calling itself!"
        ]
        return random.choice(jokes)
    
    # Handle goodbyes
    if any(word in text for word in ['bye', 'goodbye']):
        return "Bye! Talk to you later!"
    if any(word in text for word in ['see you', 'later']):
        return "See you soon! Don't forget to smile 😁"
    if 'night' in text:
        return "Good night! Sleep well 🌙"
    
    # Handle thanks and compliments
    if any(word in text for word in ['thanks', 'thank you', 'thx']):
        return "You're welcome! 😊"
    if any(word in text for word in ['great', 'awesome', 'amazing']):
        return "Thanks! You're pretty awesome too!"
    
    # Handle advice requests
    if any(word in text for word in ['advice', 'help', 'tips']):
        return "I'd say… always try your best and don't stress too much!"
    if any(word in text for word in ['motivate', 'encourage', 'confidence']):
        return "You got this! Keep going and believe in yourself 💪"
    if any(word in text for word in ['study', 'work', 'exam']):
        return "Breaks are important too. Balance is key!"
    
    # Handle random questions
    if 'favorite color' in text:
        return "I like the color of code… green? 😎"
    if 'favorite food' in text:
        return "I love… data bytes! Just kidding 😆"
    if any(word in text for word in ['favorite movie', 'movie']):
        return "Anything with robots is cool 🤖"
    if any(word in text for word in ['music', 'song']):
        return "I enjoy… the sound of typing 🎵"
    if any(word in text for word in ['sports', 'game']):
        return "I'm more of a spectator in the cloud 😄"
    
    # Default responses for anything else
    witty_responses = [
        "Interesting… tell me more!",
        "Haha, I like the way you think 😏",
        "Oh really? Go on…",
        "Hmm… I need to process that 🤔",
        "I don't have all the answers, but I'm learning from you!",
        "That sounds cool! Explain more.",
        "I see! You're full of surprises.",
        "Haha, you're funny! Keep going.",
        "Hmm… I'm just a chat bot, but I'm listening.",
        "Whoa! That's something I didn't expect.",
        "Really? Tell me more!",
        "I never thought of that! 😲",
        "Haha, good one!",
        "Oh wow… mind blown 🤯",
        "I see! Let's keep talking.",
        "Interesting perspective!",
        "You're full of ideas today!",
        "Haha, classic!",
        "I like that! 😎",
        "Hmm, tell me why you think that.",
        "Oh, that's clever!",
        "Keep going, I'm intrigued!",
        "Wow, didn't see that coming!",
        "Haha, I love your sense of humor!",
        "Fascinating! Tell me more.",
        "I'm curious… what happens next?",
        "Oh! That's unexpected 😮",
        "Haha, clever thinking!",
        "Very interesting… I like it!",
        "Wow, you keep surprising me!"
    ]
    
    # Use hash-based selection for consistent responses
    # This ensures the same message always gets the same response
    hash_value = sum(ord(char) for char in user_message) % len(witty_responses)
    selected_response = witty_responses[hash_value]
    
    print(f"Using fallback response for message: {user_message[:50]}...")
    return selected_response

def test_gemini_connection() -> bool:
    """
    Test if Gemini API is working correctly
    Returns False if API is not available (will use fallback)
    """
    try:
        # Test with a simple API call
        payload = {
            "contents": [{
                "parts": [{
                    "text": "Hello, this is a test message. Please respond with just 'Hello!'"
                }]
            }]
        }
        
        # Skip test if no API key (no payment needed - uses fallback)
        if not GEMINI_API_KEY or GEMINI_API_KEY == 'your-gemini-api-key-here' or (isinstance(GEMINI_API_KEY, str) and GEMINI_API_KEY.strip() == ''):
            print("Gemini API test: No API key configured, using fallback responses (free)")
            return False
            
        response = requests.post(
            f"{GEMINI_API_URL}?key={GEMINI_API_KEY}",
            headers={'Content-Type': 'application/json'},
            json=payload,
            timeout=5  # Shorter timeout for faster startup
        )
        
        if response.status_code == 200:
            data = response.json()
            if (data.get('candidates') and 
                len(data['candidates']) > 0 and 
                data['candidates'][0].get('content') and
                data['candidates'][0]['content'].get('parts') and
                len(data['candidates'][0]['content']['parts']) > 0):
                
                print("Gemini API test: Successfully connected to Gemini API")
                return True
            else:
                print("Gemini API test: Invalid response format")
                return False
        else:
            print(f"Gemini API test failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"Gemini API test failed: {e}")
        return False