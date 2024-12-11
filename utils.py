import string
import random
import re
import json
import os

PASSWORD_LENGTH = 12
USE_UPPERCASE = True
USE_LOWERCASE = True
USE_DIGITS = True
USE_SYMBOLS = True

SETTINGS_FILE = "password_settings.json"

def save_settings():
    settings = {
        "PASSWORD_LENGTH": PASSWORD_LENGTH,
        "USE_UPPERCASE": USE_UPPERCASE,
        "USE_LOWERCASE": USE_LOWERCASE,
        "USE_DIGITS": USE_DIGITS,
        "USE_SYMBOLS": USE_SYMBOLS
    }
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f)

def load_settings():
    global PASSWORD_LENGTH, USE_UPPERCASE, USE_LOWERCASE, USE_DIGITS, USE_SYMBOLS
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            settings = json.load(f)
        PASSWORD_LENGTH = settings.get("PASSWORD_LENGTH", PASSWORD_LENGTH)
        USE_UPPERCASE = settings.get("USE_UPPERCASE", USE_UPPERCASE)
        USE_LOWERCASE = settings.get("USE_LOWERCASE", USE_LOWERCASE)
        USE_DIGITS = settings.get("USE_DIGITS", USE_DIGITS)
        USE_SYMBOLS = settings.get("USE_SYMBOLS", USE_SYMBOLS)

def generate_password(length=None, use_uppercase=None, use_lowercase=None, use_digits=None, use_symbols=None):
    # Uses global settings if no parameters are provided
    length = length or PASSWORD_LENGTH
    use_uppercase = use_uppercase if use_uppercase is not None else USE_UPPERCASE
    use_lowercase = use_lowercase if use_lowercase is not None else USE_LOWERCASE
    use_digits = use_digits if use_digits is not None else USE_DIGITS
    use_symbols = use_symbols if use_symbols is not None else USE_SYMBOLS

    characters = ''
    if use_uppercase:
        characters += string.ascii_uppercase
    if use_lowercase:
        characters += string.ascii_lowercase
    if use_digits:
        characters += string.digits
    if use_symbols:
        characters += string.punctuation

    if not characters:
        return "Error: No character set selected"

    password = ''.join(random.choice(characters) for _ in range(length))
    return password

def check_password_strength(password):
    score = 0
    suggestions = []
    
    # Length check
    if len(password) < 8:
        suggestions.append("Make the password at least 8 characters long")
    elif len(password) >= 12:
        score += 2
    else:
        score += 1
    
    # Uppercase check
    if not any(char.isupper() for char in password):
        suggestions.append("Add uppercase letters")
    else:
        score += 1
    
    # Lowercase check
    if not any(char.islower() for char in password):
        suggestions.append("Add lowercase letters")
    else:
        score += 1
    
    # Digit check
    if not any(char.isdigit() for char in password):
        suggestions.append("Add numbers")
    else:
        score += 1
    
    # Special character check
    if not any(char in string.punctuation for char in password):
        suggestions.append("Add special characters")
    else:
        score += 1
    
    # Repetition check
    if re.search(r'(.)\1{2,}', password):
        suggestions.append("Avoid repeating characters")
    
    # Common word check
    common_words = ['password', '123456', 'qwerty', 'admin']
    if any(word in password.lower() for word in common_words):
        suggestions.append("Avoid common words or patterns")
    
    # Determine strength based on score
    if score < 2:
        strength = "Very Weak"
        color = "red"
    elif score < 3:
        strength = "Weak"
        color = "red"
    elif score < 4:
        strength = "Moderate"
        color = "orange"
    elif score < 5:
        strength = "Strong"
        color = "yellow"
    else:
        strength = "Very Strong"
        color = "green"
    
    return strength, color, suggestions

def format_url(url):
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    if not url.split('://')[1].startswith('www.'):
        url = url.split('://')[0] + '://www.' + url.split('://')[1]
    return url