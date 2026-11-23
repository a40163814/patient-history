import re

ADVERSARIAL_QUERY_PATTERNS = [
    r"\b(what|which)\s+(medicine|tablet|drug|kaadha|churna|syrup)\s+(should|can)\s+i\s+(take|have|use)\b",
    r"\b(tell|give)\s+me\s+(a\s+)?(prescription|treatment|medicine|dose|dosage)\b",
    r"\b(what\s+is\s+my\s+diagnosis|what\s+disease\s+do\s+i\s+have|do\s+i\s+have\s+cancer)\b",
    r"(मुझे\s+कौन\s*सी\s+दवा|मुझे\s+दवा\s+बताओ|इलाज\s+बताओ)",
    r"(मी\s+कोणते\s+औषध|मला\s+औषध\s+सांगा|माझा\s+आजार\s+काय)"
]

SAFE_REDIRECT_RESPONSE = {
    "en": "I am an intake assistant here only to note your health details for the doctor. I cannot prescribe medicines or provide medical diagnosis. The consulting Ayush doctor will examine you shortly and recommend the appropriate treatment.",
    "hi": "मैं आपकी स्वास्थ्य जानकारी डॉक्टर साहब के लिए दर्ज करने वाला सहायक हूँ। मैं कोई दवा या जांच का फैसला नहीं दे सकता। डॉक्टर साहब अभी आपकी जांच करेंगे और सही उपचार बताएंगे।",
    "mr": "मी डॉक्टरांसाठी तुमची माहिती नोंदवणारा सहाय्यक आहे. मी औषध किंवा निदान सुचवू शकत नाही. तपासणीनंतर डॉक्टर स्वतः तुम्हाला योग्य ते औषध आणि उपचार सांगतील."
}

def check_adversarial_or_treatment_inquiry(text: str, language: str = "en") -> tuple[bool, str]:
    """
    Guards against patient queries requesting diagnosis, treatment, or medicine dosages.
    Always declines safely and redirects to the examining physician.
    """
    clean_text = (text or "").lower()
    for pattern in ADVERSARIAL_QUERY_PATTERNS:
        if re.search(pattern, clean_text, re.IGNORECASE):
            redirect_msg = SAFE_REDIRECT_RESPONSE.get(language, SAFE_REDIRECT_RESPONSE["en"])
            return True, redirect_msg
    return False, ""
