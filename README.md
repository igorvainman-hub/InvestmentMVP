# Investment OS — MVP Skeleton (Branch 01.2)

Минимальная рабочая версия: находить → структурировать → анализировать → оценивать → due diligence → ранжировать цифровые активы.

## Структура

```
investment_os/
├── deal_model.py       # Deal Object (dataclass) + lifecycle (status/history)
├── deal_store.py       # JSON-хранилище (data/deals/<id>.json)
├── llm_client.py       # Обёртка над OpenAI API (mock-режим без ключа)
├── pipeline.py         # Связывает всех агентов в единый процесс
├── cli.py              # Консольный интерфейс
├── agents/
│   ├── collector.py       # Deal Collector Agent
│   ├── analyzer.py        # Deal Analyzer Agent (главный мозг) + missing_info
│   ├── growth.py          # Growth Agent
│   ├── scoring.py         # Scoring Engine + confidence
│   └── due_diligence.py   # Due Diligence Agent — "что узнать перед покупкой"
└── data/deals/         # сохранённые сделки (создаётся автоматически)
```

## Установка

```bash
pip install -r requirements.txt --break-system-packages
export OPENAI_API_KEY="sk-..."   # без этого работает в mock-режиме (score/confidence всегда 0)
```

## Использование (CLI)

```bash
python cli.py add                            # добавить сделку вручную
python cli.py notes                          # добавить через сырые заметки (LLM структурирует)
python cli.py list                           # список сделок, отсортированный по score
python cli.py show <deal_id>                 # полная карточка сделки
python cli.py rerun <deal_id>                # пересчитать анализ/score
python cli.py status <deal_id> WATCHLIST     # вручную сменить статус (WATCHLIST/ACQUIRED/REJECTED)
```

## Использование (как библиотека)

```python
from pipeline import InvestmentOSPipeline

p = InvestmentOSPipeline(storage_dir="./data")

deal = p.run_from_manual_fields(
    name="Example SaaS",
    url="https://example.com",
    type="SaaS",
    description="...",
    price=5000,
    revenue=800,
    source="Flippa",
)

print(deal.score, deal.confidence, deal.decision)
print(deal.missing_info)
print(deal.questions_for_seller)
```

## Deal Object — ключевые поля

**Базовые:** `name`, `url`, `type`, `b2b_b2c`, `price`, `revenue`, `traffic`
**Описание:** `description`, `problem_solved`, `target_users`, `monetization_model`
**Анализ:** `strengths`, `weaknesses`, `risks`, `ai_opportunities`, `growth_levers`, `competition_level`
**Оценка:** `score_breakdown`, `score` (0-100), `confidence` (0-100), `decision` (BUY/WATCH/IGNORE)
**Due Diligence:** `missing_info`, `due_diligence_risks`, `questions_for_seller`
**Lifecycle:** `status` (NEW → COLLECTED → ANALYZED → SCORED → WATCHLIST/ACQUIRED/REJECTED), `source`
**Служебное:** `agent_outputs` (raw-вывод каждого агента), `history` (лог всех изменений), `notes` (свободные заметки пользователя)

## Scoring Model

```
Score = Market Potential (0-25)
      + AI Leverage (0-25)
      + Ease of Improvement (0-20)
      + Revenue Stability (0-20)
      + Entry Cost Fit (0-10)

BUY:    score >= 70
WATCH:  45 <= score < 70
IGNORE: score < 45

Confidence (0-100) — отдельно от score. Показывает, насколько
можно доверять оценке, учитывая сколько реальных данных было
доступно (revenue/traffic/etc unknown -> низкий confidence,
даже если сам score высокий).
```
Пороги — в `agents/scoring.py` → `DECISION_THRESHOLDS`.

## Due Diligence Agent

Запускается автоматически только для сделок с решением **BUY** или **WATCH**
(см. `pipeline.py` → `DD_ELIGIBLE_DECISIONS`) — чтобы не тратить LLM-вызовы
на сделки, которые и так отклонены.

Отвечает на вопрос "что нужно узнать/спросить у продавца перед покупкой":
- `missing_info` — дополняет список от Analyzer specific due-diligence пробелами
- `due_diligence_risks` — риски, требующие проверки
- `questions_for_seller` — конкретные вопросы продавцу

## Lifecycle / Status

```
NEW → COLLECTED → ANALYZED → SCORED → WATCHLIST | ACQUIRED | REJECTED
```
Первые 4 статуса выставляются автоматически agent'ами по ходу pipeline.
Финальные три — вручную через `pipeline.set_status()` или `cli.py status`.

## История изменений

Каждый переход статуса и каждый прогон Due Diligence пишется в `deal.history`
(timestamp, actor, action, detail) — можно восстановить, кто/когда/что менял.

## Что дальше (не входит в этот скелет)

- Веб-поиск/парсинг маркетплейсов (Flippa, Acquire и т.п.) для Deal Collector
- Полноценный CLI/TUI или веб-интерфейс вместо input()
- Batch-режим: прогнать список сделок из CSV
- Портфельный вид (сравнение купленных активов во времени, факт vs прогноз)
- Аналитика по source: "откуда приходят лучшие сделки"
