from langchain_groq import ChatGroq
from langchain_classic.chains import LLMChain
from langchain_classic.memory import ConversationBufferWindowMemory
from app.prompt import prompt_template
from app.config import TEMPERATURE, GROQ_API_KEY, MAX_TOKENS
import re

memory = ConversationBufferWindowMemory(
    k=20, 
    memory_key="chat_history",
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
    prompt=prompt_template,
    memory=memory
)
def get_llm_response(question: str, context: str) -> str:

    # 🔹 Detect word limit from question
    question_text = question.lower()
    match = re.search(r"in\s+(\d+)\s+words?", question_text)

    word_limit = int(match.group(1)) if match else None

    # 🔹 Prepare input
    input_text = f"""
Question:
{question}

Context:
{context}
""".strip()

    result = llm_chain.invoke({
        "input_text": input_text
    })

    answer = result["text"].strip()

    # 🔥 PROFESSIONAL WORD CONTROL
    if word_limit:

        words = answer.split()

        # Retry once if mismatch
        if len(words) != word_limit:

            retry_input = f"""
Question:
{question}

Context:
{context}

Instruction:
Rewrite the answer in EXACTLY {word_limit} words.
""".strip()

            retry_result = llm_chain.invoke({
                "input_text": retry_input
            })

            answer = retry_result["text"].strip()
            words = answer.split()

        # Final hard trim safety
        if len(words) > word_limit:
            answer = " ".join(words[:word_limit])

    return answer
           
# def get_llm_response(question: str, context: str) -> str:
#     input_text = f"""
# Question:
# {question}

# Context:
# {context}
# """.strip()

#     result = llm_chain.invoke({
#         "input_text": input_text
#     })

#     answer = result["text"]

#     return answer