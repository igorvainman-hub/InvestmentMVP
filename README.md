# Investment OS

Минимальный MVP-пайплайн для поиска, структурирования, анализа и оценки цифровых активов.

## Что умеет проект

- собирать сделки из ручного ввода или сырых заметок;
- запускать анализ через LLM;
- оценивать сделки по нескольким критериям;
- сохранять результаты в JSON-хранилище;
- поддерживать базовый CLI для работы с сделками.

## Структура проекта

- [cli.py](cli.py) — консольный интерфейс
- [pipeline.py](pipeline.py) — основной pipeline обработки
- [deal_model.py](deal_model.py) — модель сделки и жизненный цикл
- [deal_store.py](deal_store.py) — сохранение сделок в JSON
- [llm_client.py](llm_client.py) — обёртка над OpenAI
- [agents/](agents/) — Collector, Analyzer, Growth, Scoring, Due Diligence
- [agents/sources/](agents/sources/) — интеграции с внешними источниками, включая Apify/Flippa
- [data/](data/) — хранилище сделок и архивных данных

## Быстрый старт

1. Установите зависимости:

```bash
pip install -r requirements.txt
```

2. Создайте файл [.env](.env) на основе [.env.example](.env.example) и укажите значения:

```env
OPENAI_API_KEY=your_openai_api_key_here
APIFY_API_TOKEN=your_apify_token_here
```

3. Запустите CLI:

```bash
python cli.py add
python cli.py list
python cli.py show <deal_id>
```

## CLI-команды

Ниже — основные команды и их назначение.

```bash
python cli.py add
# Добавить сделку вручную через интерактивный ввод

python cli.py notes
# Добавить сделку из сырых заметок: текст будет структурирован LLM

python cli.py list
# Показать список сохранённых сделок

python cli.py show <deal_id>
# Показать полную карточку сделки по ID

python cli.py rerun <deal_id>
# Перезапустить анализ и пересчёт score для уже существующей сделки

python cli.py status <deal_id> WATCHLIST
# Изменить статус сделки вручную (например: WATCHLIST, ACQUIRED, REJECTED)
```

## Настройки и поведение

- Если `OPENAI_API_KEY` не задан, проект работает в mock-режиме и сохраняет сделку как черновик.
- `APIFY_API_TOKEN` нужен только для работы с Apify/Flippa.
- Для Flippa используется отдельный контур и не запускается автоматически.

## Ключевые понятия

- `status`: жизненный статус сделки
- `score`: итоговая оценка от 0 до 100
- `confidence`: уверенность в оценке
- `decision`: BUY / WATCH / IGNORE
- `missing_info` и `questions_for_seller`: данные для due diligence

## Примечание

Проект находится в стадии MVP: основное внимание уделено рабочему пайплайну, структуре данных и базовой логике оценки.
