import pytest
from typing import List, Dict
from libs.prompt_chains import detect_intent, generate_chat_response, process_user_message
from config import *

# Mock chat history for testing
MOCK_CHAT_HISTORY: List[Dict] = [
    {"role": "user", "text": "안녕하세요", "timestamp": "2024-01-01T00:00:00"},
    {"role": "assistant", "text": "안녕하세요! 무엇을 도와드릴까요?", "timestamp": "2024-01-01T00:00:01"}
]

# Test cases for different intents
TEST_CASES = [
    # Format: (utterance, expected_intent, expected_params)
    ("오늘 날씨 어때?", "chat", {}),
    ("내일 일정 알려줘", "schedule", {"date": "tomorrow"}),
    ("어제 찍은 사진 보여줘", "photo", {"photo_date": "2024-02-13"}),  # Assumes today is 2024-02-14
    ("주식 시장 뉴스 찾아줘", "news", {}),
]

@pytest.mark.parametrize("utterance,expected_intent,expected_params", TEST_CASES)
def test_intent_detection(utterance: str, expected_intent: str, expected_params: Dict):
    """Test intent detection for various utterances"""
    intent, params = detect_intent(utterance)
    print(f"\nTesting utterance: {utterance}")
    print(f"Detected intent: {intent}")
    print(f"Detected params: {params}")
    
    assert intent == expected_intent
    # We don't assert exact params match as they might contain dynamic dates
    if expected_params:
        for key in expected_params:
            assert key in params

def test_chat_response():
    """Test chat response generation"""
    utterance = "너는 누구니?"
    response = generate_chat_response("test_user", utterance, MOCK_CHAT_HISTORY)
    print(f"\nTesting chat response")
    print(f"User: {utterance}")
    print(f"Assistant: {response}")
    
    assert response is not None
    assert len(response) > 0
    assert "자비스" in response.lower()  # Should mention its name

def test_full_conversation_flow():
    """Test a full conversation flow with multiple turns"""
    user_id = "test_user"
    utterances = [
        "안녕하세요",
        "오늘 기분이 어때?",
        "내일 일정 알려줘"  # This should trigger schedule intent
    ]
    
    print("\nTesting full conversation flow:")
    chat_history = []
    
    for utterance in utterances:
        print(f"\nUser: {utterance}")
        response, body = process_user_message(user_id, utterance, chat_history)
        print(f"Assistant: {response}")
        
        # Add to mock chat history
        chat_history.extend([
            {"role": "user", "text": utterance, "timestamp": "2024-01-01T00:00:00"},
            {"role": "assistant", "text": response, "timestamp": "2024-01-01T00:00:01"}
        ])
        
        assert response is not None
        assert len(response) > 0

if __name__ == "__main__":
    # Run tests with more detailed output
    print("Running intent detection tests...")
    for utterance, expected_intent, expected_params in TEST_CASES:
        test_intent_detection(utterance, expected_intent, expected_params)
    
    print("\nRunning chat response test...")
    test_chat_response()
    
    print("\nRunning full conversation flow test...")
    test_full_conversation_flow() 