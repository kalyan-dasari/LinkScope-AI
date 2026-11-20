from groq import Groq
from app.config import settings

client = Groq(api_key=settings.groq_api_key)
candidates = ['openai/gpt-oss-120b', 'openai/gpt-oss-20b', 'qwen/qwen3.8-27b']

for model in candidates:
    try:
        print(f"Testing {model}...")
        res = client.chat.completions.create(
            model=model,
            messages=[{'role': 'user', 'content': 'Output valid JSON: {"status": "ok"}'}],
            response_format={'type': 'json_object'}
        )
        print(f"Model {model}: SUCCESS -> {res.choices[0].message.content}")
    except Exception as e:
        print(f"Model {model}: FAILED -> {e}")
