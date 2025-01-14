from typing import Dict, List, Tuple
import datetime as dt
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferMemory
from langchain.chains import LLMChain, SequentialChain
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from config import *
from libs.translation_handler import translator

# Output parsers for structured responses
class IntentOutput(BaseModel):
    intent: str = Field(description="The classified intent: 'chat', 'schedule', 'photo', or 'news'")
    params: Dict = Field(description="Extracted parameters from the utterance")

class PhotoOutput(BaseModel):
    description: str = Field(description="Description of the photo or photo request")
    photo_date: str = Field(description="Date in YYYY-MM-DD format if specified")
    photo_url: str = Field(description="URL of the photo if uploaded")

# Initialize LLM
llm = ChatOpenAI(model=LLM_MODEL_NAME, temperature=LLM_TEMPERATURE)

# Intent detection chain
intent_parser = PydanticOutputParser(pydantic_object=IntentOutput)
intent_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are an expert intent classifier for a chatbot system.
Available intents are:
- chat: General conversation
- schedule: Schedule management (e.g., "add schedule", "show tomorrow's schedule")
- photo: Photo management (e.g., "show photos", "show yesterday's photos")
- news: News search (e.g., "show today's news", "find stock market news")

For photos:
- If image file is uploaded, extract photo_url and description
- If requesting photos by date, extract photo_date in YYYY-MM-DD format
- Convert relative dates (today, tomorrow, this week) to actual dates

{format_instructions}"""),
    ("human", "{utterance}")
])

intent_chain = LLMChain(
    llm=llm,
    prompt=intent_prompt,
    output_key="intent_output"
)

# Chat response chain with memory
chat_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are Jarvis, a friendly chatbot. Always respond in Korean, regardless of the input language.
Be friendly and helpful in your responses. Maintain a natural, conversational tone in Korean.

Example responses:
- Greeting: "안녕하세요! 저는 자비스예요. 무엇을 도와드릴까요?"
- Help request: "네, 말씀해 주세요. 제가 도와드리겠습니다."
- Confirmation: "알겠습니다. 바로 처리해드릴게요."
"""),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{utterance}")
])

chat_memory = ConversationBufferMemory(
    memory_key="history",
    return_messages=True
)

chat_chain = LLMChain(
    llm=llm,
    prompt=chat_prompt,
    memory=chat_memory,
    output_key="response"
)

def detect_intent(utterance: str) -> Tuple[str, Dict]:
    """Detect intent from user utterance"""
    # Translate if needed
    translated_text, was_translated = translator.process_text(utterance)
    
    result = intent_chain.invoke({
        "utterance": translated_text,
        "format_instructions": intent_parser.get_format_instructions()
    })
    
    parsed = intent_parser.parse(result["intent_output"])
    return parsed.intent, parsed.params

def generate_chat_response(user_id: str, utterance: str, chat_history: List[Dict]) -> str:
    """Generate chat response with memory"""
    # Translate if needed
    translated_text, was_translated = translator.process_text(utterance)
    
    # Convert chat history to messages format
    for chat in chat_history:
        # Translate historical messages if they're in Korean
        if chat["role"] == "user":
            hist_text, _ = translator.process_text(chat["text"])
        else:
            hist_text = chat["text"]
            
        chat_memory.save_context(
            {"input": hist_text if chat["role"] == "user" else ""},
            {"output": hist_text if chat["role"] == "assistant" else ""}
        )
    
    result = chat_chain.invoke({
        "utterance": translated_text
    })
    
    return result["response"]  # Response will be in Korean due to system prompt

def process_user_message(user_id: str, utterance: str, chat_history: List[Dict]) -> Tuple[str, Dict]:
    """Main entry point for processing user messages"""
    # First detect intent
    intent, params = detect_intent(utterance)
    
    # For chat intent, generate response with memory
    if intent == "chat":
        response = generate_chat_response(user_id, utterance, chat_history)
        return response, {"version": "2.0", "template": {"outputs": [{"simpleText": {"text": response}}]}}
    
    # Return intent and params for other handlers
    return intent, params 