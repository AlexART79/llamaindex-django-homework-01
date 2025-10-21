from dotenv import load_dotenv
from llama_index.llms.openai import OpenAI
from functools import lru_cache

load_dotenv()

def call_llm(prompt: str):
    llm = OpenAI(
        model="gpt-4o-mini",
        temperature=0
    )

    res = llm.complete(prompt)
    return res

@lru_cache(maxsize=128)
def call_llm_cached(prompt: str):
    return call_llm(prompt)