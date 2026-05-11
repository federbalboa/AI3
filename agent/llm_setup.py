import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

def get_llm(llm_type_override=None, ollama_model_override=None):
    llm_type = llm_type_override.lower() if llm_type_override else os.getenv("LLM_TYPE", "gemini").lower()
    
    if llm_type == "ollama":
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        model = ollama_model_override if ollama_model_override else os.getenv("OLLAMA_MODEL", "llama3")
        return ChatOllama(base_url=base_url, model=model, temperature=0.2)
    elif llm_type == "openai":
        api_key = os.getenv("OPENAI_API_KEY", "")
        if not api_key or api_key == "tu_api_key_aqui":
            raise ValueError("Por favor configura OPENAI_API_KEY en tu archivo .env")
        return ChatOpenAI(api_key=api_key, model="gpt-4o-mini", temperature=0.2)
    elif llm_type == "gemini":
        api_key = os.getenv("GEMINI_API_KEY", "")
        if not api_key or api_key == "tu_api_key_aqui":
            raise ValueError("Por favor configura GEMINI_API_KEY en tu archivo .env")
        return ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=api_key, temperature=0.2)
    else:
        raise ValueError("Tipo de LLM no soportado. Revisa LLM_TYPE en .env")
