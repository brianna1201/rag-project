import pytest
from libs.translation_handler import translator

TEST_CASES = [
    # (input_text, expected_is_korean)
    ("안녕하세요", True),
    ("Hello, how are you?", False),
    ("오늘 날씨가 좋네요", True),
    ("Mixed 한글 and English", False),  # 한글 비율이 낮아서 한글로 판단하지 않음
    ("Today is a good day", False),
]

@pytest.mark.parametrize("text,expected_is_korean", TEST_CASES)
def test_language_detection(text: str, expected_is_korean: bool):
    """Test language detection functionality"""
    is_korean, confidence = translator.detect_language(text)
    print(f"\nTesting text: {text}")
    print(f"Detected Korean: {is_korean} (confidence: {confidence})")
    
    assert is_korean == expected_is_korean
    assert 0 <= confidence <= 1

def test_translation():
    """Test Korean to English translation"""
    korean_texts = [
        "안녕하세요, 오늘 날씨가 좋네요",
        "내일 일정을 알려주세요",
        "사진을 보여주세요"
    ]
    
    print("\nTesting translations:")
    for text in korean_texts:
        translated, was_translated = translator.process_text(text)
        print(f"\nKorean: {text}")
        print(f"English: {translated}")
        
        assert was_translated
        assert translated != text
        assert len(translated) > 0

def test_end_to_end_flow():
    """Test the complete translation flow with different inputs"""
    test_inputs = [
        ("Hello, how are you?", False),  # English input
        ("안녕하세요, 날씨가 좋네요", True),  # Korean input
        ("Show me the schedule", False),  # English command
        ("일정 보여주세요", True),  # Korean command
    ]
    
    print("\nTesting end-to-end flow:")
    for text, should_translate in test_inputs:
        translated, was_translated = translator.process_text(text)
        print(f"\nInput: {text}")
        print(f"Output: {translated}")
        print(f"Was translated: {was_translated}")
        
        assert was_translated == should_translate
        if not should_translate:
            assert translated == text

if __name__ == "__main__":
    # Run tests with more detailed output
    print("Running language detection tests...")
    for text, expected in TEST_CASES:
        test_language_detection(text, expected)
    
    print("\nRunning translation tests...")
    test_translation()
    
    print("\nRunning end-to-end flow tests...")
    test_end_to_end_flow() 