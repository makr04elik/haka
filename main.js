const API_URL = "https://openrouter.ai/api/v1/chat/completions";
const MODEL = "meta-llama/llama-3.2-3b-instruct:free";
const OPENROUTER_API_KEY = "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";

async function loadAllGeoJSONs() {
  try {
    const response = await fetch("data/list.json");
    if (!response.ok) throw new Error(`Не найден list.json (${response.status})`);
    const files = await response.json();

    const allFeatures = [];
    for (const file of files) {
      try {
        const res = await fetch(`data/${file}`);
        if (!res.ok) continue;
        const geojson = await res.json();
        if (geojson.type === "FeatureCollection") {
          allFeatures.push(...geojson.features);
        }
      } catch (e) {
        console.warn("⚠️ Ошибка при чтении:", file, e);
      }
    }
    return allFeatures;
  } catch (e) {
    console.error("Ошибка загрузки list.json:", e);
    return [];
  }
}

async function findRoadSegmentSmart(userQuery) {
  try {
    const response = await fetch("data/list.json");
    if (!response.ok) throw new Error(`Не найден list.json (${response.status})`);
    const files = await response.json();

    const query = userQuery.toLowerCase();

    for (const file of files) {
      const res = await fetch(`data/${file}`);
      if (!res.ok) continue;

      const geojson = await res.json();
      if (geojson.type !== "FeatureCollection") continue;

      for (const f of geojson.features) {
        const p = f.properties || {};
        const st = (p.ST_NAME || "").toLowerCase();
        const cf = (p.CrossNameF || "").toLowerCase();
        const ct = (p.CrossNameT || "").toLowerCase();

        if (
          query.includes(st) ||
          query.includes(cf) ||
          query.includes(ct) ||
          (p.EdgeId && query.includes(String(p.EdgeId)))
        ) {
          console.log("✅ Найден в файле:", file);
          return p;
        }
      }
    }

    return null;
  } catch (e) {
    console.error("Ошибка при поиске:", e);
    return null;
  }
}


async function analyze() {
  const output = document.getElementById("output");
  const userQuery = document.getElementById("userQuery").value.trim();

  if (!userQuery) {
    output.textContent = "⚠️ Введите запрос.";
    return;
  }

  output.textContent = "📂 Загрузка GeoJSON...\n";

  const segment = await findRoadSegmentSmart(userQuery);
if (!segment) {
  output.textContent = "❌ Не найден участок, соответствующий запросу.";
  return;
}

  output.textContent = "🔍 Выполняется анализ, пожалуйста подождите...\n";

  const userPrompt = `
Ты — URBANAI ADVISOR, эксперт по транспортному планированию. 
Ты идеально владеешь русским языком и никогда не используешь другие языки.

Используй данные ниже, чтобы сделать реальный анализ дорожной ситуации.

Составь отчёт без лишних рассуждений: анализ, причины, прогноз, рекомендации.

Запрос пользователя: ${userQuery}

Данные об участке:
${JSON.stringify(segment, null, 2)}
`;

  const payload = {
    model: MODEL,
    messages: [{ role: "user", content: userPrompt }],
    temperature: 0.7,
    max_tokens: 900
  };

  try {
    const res = await fetch(API_URL, {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${OPENROUTER_API_KEY}`,
        "Content-Type": "application/json",
        "X-Title": "URBANAI-ADVISOR"
      },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      const text = await res.text();
      output.textContent = `⚠️ Ошибка API (${res.status}): ${text}`;
      return;
    }

    const data = await res.json();
    const content = data.choices?.[0]?.message?.content?.trim();
    output.textContent = content
      ? "🤖 URBANAI ADVISOR:\n\n" + content
      : "⚠️ Пустой ответ от модели.";
  } catch (err) {
    output.textContent = "⚠️ Ошибка запроса: " + err.message;
  }
}
