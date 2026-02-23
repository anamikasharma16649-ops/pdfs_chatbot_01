from langchain_groq import ChatGroq
from langchain_classic.chains import LLMChain
from langchain_classic.memory import ConversationBufferWindowMemory
from app.prompt import prompt_template
from app.config import TEMPERATURE, GROQ_API_KEY, MAX_TOKENS
from typing import Optional

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
def get_llm_response(question: str, context: str, word_limit: Optional[int] = None) -> str:
    input_text = f"""
Question:
{question}

Context:
{context}
""".strip()

    result = llm_chain.invoke({
        "input_text": input_text
    })

    answer = result["text"]

    if word_limit:
        answer = " ".join(answer.split()[:word_limit])

    return answer