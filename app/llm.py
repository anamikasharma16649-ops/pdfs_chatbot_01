# from langchain_groq import ChatGroq
# from langchain_classic.chains import LLMChain
# from langchain_classic.memory import ConversationBufferWindowMemory
# from app.prompt import prompt_template
# from app.formatter import format_text
# from app.config import TEMPERATURE, GROQ_API_KEY, MAX_TOKENS
# import re

# def build_memory():
#     return ConversationBufferWindowMemory(
#     k=20, 
#     memory_key="chat_history",
#     input_key="question",
#     return_messages=True
# )

# llm = ChatGroq(
#     groq_api_key=GROQ_API_KEY,
#     model_name="openai/gpt-oss-120b",
#     temperature=TEMPERATURE,
#     max_tokens=MAX_TOKENS
# )

# llm_chain = LLMChain(
#     llm=llm,
#     prompt=prompt_template
# )

# def get_llm_response(question: str, context: str, memory) -> str:
#     # ... existing code ...
    
#     question_text = question.lower()
#     match = re.search(r"in\s+(\d+)\s+words?", question_text)
#     word_limit = int(match.group(1)) if match else None
    
#     result = llm_chain.invoke({
#         "chat_history": memory.load_memory_variables({})["chat_history"],
#         "context": context,
#         "question": question
#     })
    
#     answer = result["text"].strip()

#     print("="*50)
#     print("RAW LLM OUTPUT:")
#     print(answer)
#     print("="*50)

#     if word_limit:
#         words = answer.split()
#         if len(words) > word_limit:
#             answer = " ".join(words[:word_limit]).strip()

#     memory.save_context(
#         {"question": question},
#         {"output": answer}
#     )


#     return format_text(answer)


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
    temperature=TEMPERATURE,
    max_tokens=MAX_TOKENS
)

llm_chain = LLMChain(
    llm=llm,
    prompt=prompt_template
)

def clean_context(context: str) -> str:
    """Clean and deduplicate context"""
    context = re.sub(r'\n{3,}', '\n\n', context)
    
    # Simple sentence deduplication
    sentences = context.split('. ')
    unique_sentences = []
    seen = set()
    
    for sent in sentences:
        sent_clean = sent.strip()
        if sent_clean and sent_clean not in seen:
            seen.add(sent_clean)
            unique_sentences.append(sent_clean)
    
    return '. '.join(unique_sentences)

def clean_answer(answer: str) -> str:
    """Remove duplicate lines from answer"""
    lines = answer.split('\n')
    clean_lines = []
    seen_lines = set()
    
    for line in lines:
        line_clean = line.strip()
        # Skip empty lines
        if not line_clean:
            continue
        # Skip duplicate lines
        if line_clean not in seen_lines:
            seen_lines.add(line_clean)
            clean_lines.append(line)
    
    return '\n'.join(clean_lines)

def get_llm_response(question: str, context: str, memory) -> str:
    # Clean context first
    context = clean_context(context)
    
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

    # Remove duplicate lines
    answer = clean_answer(answer)

    if word_limit:
        words = answer.split()
        if len(words) > word_limit:
            answer = " ".join(words[:word_limit]).strip()

    memory.save_context(
        {"question": question},
        {"output": answer}
    )

    return format_text(answer)