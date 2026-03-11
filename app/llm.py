from langchain_groq import ChatGroq
from langchain_classic.chains import LLMChain
from langchain_classic.memory import ConversationBufferWindowMemory
from app.prompt import prompt_template
from app.formatter import format_text
from app.config import TEMPERATURE, GROQ_API_KEY, MAX_TOKENS
import re

def build_memory():
    return ConversationBufferWindowMemory(
    k=20, 
    memory_key="chat_history",
    input_key="question",
    return_messages=True
)

llm = ChatGroq(
    groq_api_key=GROQ_API_KEY,
    model_name="openai/gpt-oss-120b",
    # model_name="llama-3.3-70b-versatile",
    temperature=TEMPERATURE,
    max_tokens=MAX_TOKENS
)

llm_chain = LLMChain(
    llm=llm,
    prompt=prompt_template
)

def get_llm_response(question: str, context: str, memory) -> str:
    context = re.sub(r'(\w)\n(\w)', r'\1 \2', context)
    context = re.sub(r'\n+', '\n', context)
    context = context.replace("●", "-")
    
    question_text = question.lower()
    match = re.search(r"in\s+(\d+)\s+words?", question_text)
    word_limit = int(match.group(1)) if match else None
    
    result = llm_chain.invoke({
        "chat_history": memory.load_memory_variables({})["chat_history"],
        "context": context,
        "question": question
    })

    answer = result["text"].strip()

    print("="*50)
    print("RAW LLM OUTPUT:")
    print(answer)
    print("="*50)

    if word_limit:
        words = answer.split()
        if len(words) > word_limit:
            answer = " ".join(words[:word_limit]).strip()

    memory.save_context(
        {"question": question},
        {"output": answer}
    )


    return format_text(answer)
