from typing import Dict, List, Tuple
import datetime as dt
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferMemory
from langchain.chains import LLMChain, SequentialChain
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from config import *  # This will ensure environment variables are set

# Output parsers for structured responses
class IntentOutput(BaseModel):
    intent: str = Field(description="The classified intent: 'chat', 'schedule', 'photo', or 'news'")
    params: Dict = Field(description="Extracted parameters from the utterance")

class PhotoOutput(BaseModel):
    description: str = Field(description="Description of the photo or photo request")
    photo_date: str = Field(description="Date in YYYY-MM-DD format if specified")
    photo_url: str = Field(description="URL of the photo if uploaded")

# Initialize LLM
llm = ChatOpenAI(model="gpt-4-turbo-preview", temperature=0)

# Intent detection chain
intent_parser = PydanticOutputParser(pydantic_object=IntentOutput)
intent_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are an expert intent classifier for a Korean chatbot system.
Available intents are:
- chat: General conversation
- schedule: Schedule management (e.g., "일정 추가해줘", "내일 일정 알려줘")
- photo: Photo management (e.g., "사진 보여줘", "어제 찍은 사진 보여줘")
- news: News search (e.g., "오늘 뉴스 보여줘", "주식 뉴스 찾아줘")

For photos:
- If image file is uploaded, extract photo_url and description
- If requesting photos by date, extract photo_date in YYYY-MM-DD format
- Convert relative dates (오늘, 내일, 이번주) to actual dates

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
    ("system", "네 이름은 자비스야. 너는 친절한 챗봇이야. 아래 질문에 친절하게 대답해줘"),
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
    result = intent_chain.invoke({
        "utterance": utterance,
        "format_instructions": intent_parser.get_format_instructions()
    })
    
    parsed = intent_parser.parse(result["intent_output"])
    return parsed.intent, parsed.params

def generate_chat_response(user_id: str, utterance: str, chat_history: List[Dict]) -> str:
    """Generate chat response with memory"""
    # Convert chat history to messages format
    for chat in chat_history:
        chat_memory.save_context(
            {"input": chat["text"] if chat["role"] == "user" else ""},
            {"output": chat["text"] if chat["role"] == "assistant" else ""}
        )
    
    result = chat_chain.invoke({
        "utterance": utterance
    })
    
    return result["response"]

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