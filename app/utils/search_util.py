# utils/search_utils.py
import json
import os
from datetime import datetime
from duckduckgo_search import DDGS

def realizar_busca_web(query_text, max_results=5, save_dir="search_logs"):
    search_engine = DDGS()
    results = []

    try:
        for r in search_engine.text(query_text, max_results=max_results):
            results.append({
                "title": r.get("title"),
                "href": r.get("href"),
                "body": r.get("body")
            })
    except Exception as e:
        results.append({"error": str(e)})

    os.makedirs(save_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(save_dir, f"search_{timestamp}.json")
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    # Criar texto resumido para o LLM
    resumo = "\n\n".join([
        f"Título: {r['title']}\nResumo: {r.get('body', '')}"
        for r in results if r.get("title")
    ])
    return resumo, filename
