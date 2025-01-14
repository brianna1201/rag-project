from typing import Dict, Tuple
import re
from transformers import MarianMTModel, MarianTokenizer
from config import KOREAN_DETECTION_THRESHOLD, TRANSLATION_MODEL_NAME

class TranslationHandler:
    def __init__(self):
        # Initialize Korean to English translation model
        self.ko_en_model_name = TRANSLATION_MODEL_NAME
        self.ko_en_tokenizer = MarianTokenizer.from_pretrained(self.ko_en_model_name)
        self.ko_en_model = MarianMTModel.from_pretrained(self.ko_en_model_name)

    def detect_language(self, text: str) -> Tuple[bool, float]:
        """Detect if text contains Korean characters using regex"""
        # Check for Korean Unicode range (Hangul Syllables and Hangul Jamo)
        korean_pattern = re.compile('[가-힣ㄱ-ㅎㅏ-ㅣ]')
        korean_ratio = len(korean_pattern.findall(text)) / len(text.replace(" ", ""))
        is_korean = korean_ratio > KOREAN_DETECTION_THRESHOLD
        return is_korean, korean_ratio

    def translate_to_english(self, text: str) -> str:
        """Translate Korean text to English using MarianMT"""
        inputs = self.ko_en_tokenizer(text, return_tensors="pt", padding=True, truncation=True)
        translated = self.ko_en_model.generate(**inputs)
        return self.ko_en_tokenizer.decode(translated[0], skip_special_tokens=True)

    def process_text(self, text: str) -> Tuple[str, bool]:
        """Process input text, translating if necessary"""
        is_korean, _ = self.detect_language(text)
        if is_korean:
            translated = self.translate_to_english(text)
            return translated, True
        return text, False

# Singleton instance
translator = TranslationHandler() 