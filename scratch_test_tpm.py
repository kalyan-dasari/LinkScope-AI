import time
from groq import Groq
from app.config import settings

client = Groq(api_key=settings.groq_api_key)

for model in ['openai/gpt-oss-20b', 'qwen/qwen3.8-27b', 'openai/gpt-oss-120b']:
    try:
        t0 = time.perf_counter()
        res = client.chat.completions.create(
            model=model,
            messages=[{'role': 'user', 'content': 'Output valid JSON: {"test": "ok"}'}],
            max_tokens=2048,
            response_format={'type': 'json_object'}
        )
        elapsed = round(time.perf_counter() - t0, 2)
        print(f"Model '{model}' -> SUCCESS in {elapsed}s | total_tokens: {res.usage.total_tokens}")
    except Exception as e:
        print(f"Model '{model}' -> ERROR: {e}")
