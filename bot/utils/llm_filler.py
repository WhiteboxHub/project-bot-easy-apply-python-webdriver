from bot.utils.ai.openai import ai_extract_skills as openai_extract, ai_answer_question as openai_answer
from bot.utils.ai.deepseek import deepseek_extract_skills as deepseek_extract, deepseek_answer_question as deepseek_answer
from bot.utils.ai.gemini import gemini_extract_skills as gemini_extract, gemini_answer_question as gemini_answer
from bot.utils.logger import print_lg

def extract_skills(client, description, provider="openai"):
    try:
        if provider.lower() == "openai":
            return openai_extract(client, description)
        elif provider.lower() == "deepseek":
            return deepseek_extract(client, description)
        elif provider.lower() == "gemini":
            return gemini_extract(client, description)
    except Exception as e:
        print_lg(f"AI Skill Extraction failed: {e}")
    return "Unknown"

def answer_question(client, question, description, provider="openai"):
    try:
        if provider.lower() == "openai":
            return openai_answer(client, question, description)
        elif provider.lower() == "deepseek":
            return deepseek_answer(client, question, description)
        elif provider.lower() == "gemini":
            return gemini_answer(client, question, description)
    except Exception as e:
        print_lg(f"AI Question Answering failed: {e}")
    return None
