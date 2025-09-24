from typing import Dict, List, Tuple
from config import config

TONE_CHARACTERISTICS: Dict[str, Dict[str, List[str]]] = {
    "Formal": {
        "words": [
            "respectfully", "kindly", "accordingly", "pursuant", "regarding",
            "furthermore", "nevertheless", "therefore"
        ],
        "phrases": [
            "I am writing to", "please be advised", "as per our discussion",
            "thank you for your consideration", "at your earliest convenience"
        ],
        "avoid": [
            "hey", "yeah", "cool", "awesome", "thanks", "btw", "okay"
        ]
    },
    "Friendly": {
        "words": [
            "great", "wonderful", "appreciate", "thanks", "helpful",
            "excited", "looking forward", "pleased"
        ],
        "phrases": [
            "hope you're doing well", "great to hear from you",
            "thanks so much", "looking forward to", "all the best"
        ],
        "avoid": [
            "hereby", "pursuant", "moreover", "thus", "henceforth"
        ]
    },
    "Persuasive": {
        "words": [
            "opportunity", "benefit", "advantage", "valuable", "essential",
            "proven", "guaranteed", "exclusive"
        ],
        "phrases": [
            "you'll be pleased to know", "I'm confident that",
            "this will ensure", "consider the benefits", "imagine how"
        ],
        "avoid": [
            "maybe", "perhaps", "possibly", "might", "somewhat"
        ]
    },
    "Apologetic": {
        "words": [
            "apologize", "sorry", "regret", "understand", "inconvenience",
            "mistake", "error", "rectify"
        ],
        "phrases": [
            "I sincerely apologize", "please accept our apologies",
            "we understand your frustration", "we will make this right"
        ],
        "avoid": [
            "but", "however", "though", "excuse", "defend"
        ]
    },
    "Assertive": {
        "words": [
            "will", "must", "require", "ensure", "immediate",
            "essential", "crucial", "necessary"
        ],
        "phrases": [
            "I expect", "please ensure that", "it is essential",
            "this requires immediate attention", "I need"
        ],
        "avoid": [
            "maybe", "kind of", "sort of", "hopefully", "if possible"
        ]
    }
}

def normalize_tone(tone: str) -> str:
    """
    Normalize tone input to match supported tone options.

    Args:
        tone (str): Raw tone input from user or frontend.

    Returns:
        str: Validated tone string (default: "Formal").
    """
    if not tone:
        return "Formal"

    tone_clean = tone.strip().capitalize()
    if tone_clean in config.TONE_OPTIONS:
        return tone_clean
    
    # Find closest matching tone
    tone_lower = tone_clean.lower()
    for valid_tone in config.TONE_OPTIONS:
        if valid_tone.lower() in tone_lower:
            return valid_tone
    
    return "Formal"

def get_tone_characteristics(tone: str) -> Dict[str, List[str]]:
    """
    Get the characteristics for a specific tone.

    Args:
        tone (str): Validated tone string.

    Returns:
        Dict[str, List[str]]: Dictionary of tone characteristics.
    """
    return TONE_CHARACTERISTICS.get(tone, TONE_CHARACTERISTICS["Formal"])

def get_tone_prompt_prefix(tone: str) -> str:
    """
    Return a detailed prompt prefix based on tone.

    Args:
        tone (str): Validated tone string.

    Returns:
        str: Prompt modifier to guide NLP generation.
    """
    characteristics = get_tone_characteristics(tone)
    
    prompt_parts = [
        f"Write in a {tone.lower()} tone, incorporating these elements:",
        "\nPreferred words and phrases:",
        ", ".join(characteristics["words"][:3] + characteristics["phrases"][:2]),
        "\nAvoid:",
        ", ".join(characteristics["avoid"][:3]),
    ]
    
    return "\n".join(prompt_parts)

def analyze_tone(text: str) -> Tuple[str, float]:
    """
    Analyze the tone of given text and return the detected tone and confidence.

    Args:
        text (str): Text to analyze.

    Returns:
        Tuple[str, float]: Detected tone and confidence score.
    """
    text_lower = text.lower()
    scores = {}
    
    for tone, chars in TONE_CHARACTERISTICS.items():
        score = 0
        total_markers = len(chars["words"]) + len(chars["phrases"])
        
        # Check for tone-specific words and phrases
        for word in chars["words"]:
            if word.lower() in text_lower:
                score += 1
        
        for phrase in chars["phrases"]:
            if phrase.lower() in text_lower:
                score += 2  # Phrases are stronger indicators
        
        # Check for words to avoid (negative markers)
        for avoid in chars["avoid"]:
            if avoid.lower() in text_lower:
                score -= 1
        
        scores[tone] = score / total_markers
    
    # Get tone with highest score
    detected_tone = max(scores.items(), key=lambda x: x[1])
    return detected_tone[0], min(1.0, detected_tone[1])  # Cap confidence at 1.0

def adjust_tone(text: str, target_tone: str) -> str:
    """
    Adjust the tone of given text to match target tone.
    This is a placeholder for future implementation using more sophisticated NLP.
    """
    # TODO: Implement actual tone adjustment using NLP
    return text