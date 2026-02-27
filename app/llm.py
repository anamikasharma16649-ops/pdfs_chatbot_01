from langchain_groq import ChatGroq
from langchain_classic.chains import LLMChain
from langchain_classic.memory import ConversationBufferWindowMemory
from app.prompt import prompt_template
from app.config import TEMPERATURE, GROQ_API_KEY, MAX_TOKENS
import re

def build_memory():
    return ConversationBufferWindowMemory(
    k=20, 
    memory_key="chat_history",
    input_key="question",
    return_messages=False
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

def get_llm_response(question: str, context: str, memory) -> str:

    # 🔹 detect word limit
    question_text = question.lower()
    match = re.search(r"in\s+(\d+)\s+words?", question_text)
    word_limit = int(match.group(1)) if match else None

    # 🔹 LLM call (ONLY ONCE)
    result = llm_chain.invoke({
        "chat_history": memory.load_memory_variables({})["chat_history"],
        "context": context,
        "question": question
    })

    answer = result["text"].strip()

    # ✅ FINAL WORD TRIM (PRODUCTION SAFE)
    if word_limit:
        answer = re.sub(r"\s+", " ", answer).strip()
        answer = " ".join(answer.split()[:word_limit])

    return answer

# def get_llm_response(question: str, context: str) -> str:

#     # 🔹 Detect word limit from question
#     question_text = question.lower()
#     match = re.search(r"in\s+(\d+)\s+words?", question_text)

#     word_limit = int(match.group(1)) if match else None

#     # 🔹 Prepare input
# result = llm_chain.invoke({
#     "chat_history": memory.load_memory_variables({})["chat_history"],
#     "context": context,
#     "question": question
# })

# answer = result["text"].strip()

#     # 🔥 PROFESSIONAL WORD CONTROL
# if word_limit:

#     words = answer.split()

#         # Retry once if mismatch
#         if len(words) != word_limit:

#             retry_input = f"""
# Question:
# {question}

# Context:
# {context}

# Instruction:
# Rewrite the answer in EXACTLY {word_limit} words.
# """.strip()

#             retry_result = llm_chain.invoke({
#                 "input_text": retry_input
#             })

#             answer = retry_result["text"].strip()
#             words = answer.split()

#         # Final hard trim safety
#         if len(words) > word_limit:
#             answer = " ".join(words[:word_limit])

#     return answer
           
# # def get_llm_response(question: str, context: str) -> str:
# #     input_text = f"""
# # Question:
# # {question}

# # Context:
# # {context}
# # """.strip()

# #     result = llm_chain.invoke({
# #         "input_text": input_text
# #     })

# #     answer = result["text"]

# #     return answer