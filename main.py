import json
import requests
from pathlib import Path


OPENROUTER_API_KEY = "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"
API_URL = "https://openrouter.ai/api/v1/chat/completions" 


MODEL = "meta-llama/llama-3.2-3b-instruct:free"

DATA_DIR = Path("data")



def load_all_geojsons(directory: Path):
    """Загружает все файлы GeoJSON из папки."""
    all_features = []
    for file in directory.glob("*.geojson"):
        try:
            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if data.get("type") == "FeatureCollection":
                    all_features.extend(data.get("features", []))
        except Exception as e:
            print(f"⚠️ Ошибка чтения {file.name}: {e}")
    return all_features


def find_road_segment(features, user_query):
    query_lower = user_query.lower()
    best_match = None
    best_score = 0

    for feature in features:
        props = feature.get("properties", {})
        st_name = str(props.get("ST_NAME", "")).strip()
        cross_f = str(props.get("CrossNameF", "")).strip()
        cross_t = str(props.get("CrossNameT", "")).strip()

        
        st_name_lower = st_name.lower()
        cross_f_lower = cross_f.lower()
        cross_t_lower = cross_t.lower()

        score = 0

        
        if st_name_lower and st_name_lower in query_lower:
            score += 10
        elif query_lower in st_name_lower: 
            score += 8


        if cross_f_lower and cross_f_lower in query_lower:
            score += 5
        if cross_t_lower and cross_t_lower in query_lower:
            score += 5

        
        edge_id = props.get("EdgeId")
        if edge_id and str(edge_id) in query_lower:
            score += 15

        if score > best_score:
            best_score = score
            best_match = props

    return best_match if best_score > 0 else None

def analyze_with_ai(user_query, road_data):
    """Отправляет запрос к OpenRouter API с использованием Llama 3.2 3B Instruct."""
    user_prompt = (
        "Ты — URBANAI ADVISOR, эксперт по транспортному планированию. "
        "Проанализируй дорожную ситуацию, используя данные, и оформи отчёт: "
        "анализ, причины, решения, прогнозы и альтернативы.\n\n"
        f"Запрос пользователя: {user_query}\n\n"
        f"Данные об участке:\n{json.dumps(road_data, ensure_ascii=False, indent=2)}"
    )

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 900
    }

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost",
        "X-Title": "URBANAI ADVISOR"
    }

    try:
        response = requests.post(API_URL, headers=headers, data=json.dumps(payload), timeout=30)
    except requests.exceptions.RequestException as e:
        return f"⚠️ Ошибка соединения: {e}"

    if response.status_code != 200:
        return f"⚠️ Ошибка API ({response.status_code}): {response.text}"

    try:
        return response.json()["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError) as e:
        return f"⚠️ Ошибка обработки ответа: {e}\nПолный ответ: {response.text}"


def main():
    print("🤖 URBANAI ADVISOR — Анализ дорожной ситуации")
    print("Введите запрос, например: 'Проанализируй участок Ленинского проспекта от д.50 до д.100'")
    user_query = input("👤 ПОЛЬЗОВАТЕЛЬ: ")

    print("\n📂 Загрузка всех GeoJSON файлов из папки 'data/'...")
    features = load_all_geojsons(DATA_DIR)

    if not features:
        print("❌ В папке 'data/' нет файлов GeoJSON.")
        return

    segment = find_road_segment(features, user_query)

    if not segment:
        print("❌ Не удалось найти участок дороги, соответствующий запросу.")
        print("💡 Убедитесь, что в запросе есть и название дороги (например, 'Ленинский проспект'), и сегмент (например, 'от д.50 до д.100').")
        return

    print("\n🔍 Выполняется анализ, подождите...\n")

    result = analyze_with_ai(user_query, segment)

    print("\n🤖 URBANAI ADVISOR:\n")
    print(result)


if name == "main":
    main()