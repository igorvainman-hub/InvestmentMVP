# Investment OS

An MVP pipeline for discovering, structuring, analyzing, and scoring digital assets (SaaS, websites, extensions, APIs).

## Features

- Manual deal entry or import from raw notes
- Flippa listing import via Apify
- Automated normalization and archival
- LLM-powered analysis
- Multi-criteria deal scoring
- JSON-based deal storage
- CLI for deal management

## Project Structure

- [cli.py](cli.py) — Command-line interface
- [pipeline.py](pipeline.py) — Deal processing pipeline
- [deal_model.py](deal_model.py) — Deal model and lifecycle
- [deal_store.py](deal_store.py) — JSON storage layer
- [llm_client.py](llm_client.py) — OpenAI wrapper
- [agents/](agents/) — Collector, Analyzer, Growth, Scoring, Due Diligence agents
- [agents/sources/](agents/sources/) — External integrations (Apify, Flippa)
- [data/](data/) — Deal storage and archives

## Quick Start

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Create `.env` from `.env.example` and set your keys:

```env
OPENAI_API_KEY=your_openai_api_key_here
APIFY_API_TOKEN=your_apify_token_here
```

3. Run CLI commands:

```bash
python cli.py add              # Add deal manually
python cli.py flippa           # Import and analyze Flippa listings
python cli.py list             # Show all deals
python cli.py show <deal_id>   # View deal details
```

## CLI Commands

```bash
python cli.py add
# Add a deal manually via interactive input

python cli.py notes
# Add deal from raw notes (LLM-structured)

python cli.py flippa
# Import Flippa listings via Apify and run full pipeline

python cli.py flippa-only
# Import Flippa listings only (skip analysis and scoring)

python cli.py list
# List all saved deals

python cli.py show <deal_id>
# Display full deal card

python cli.py rerun <deal_id>
# Re-analyze and re-score an existing deal

python cli.py status <deal_id> STATUS
# Change deal status (WATCHLIST, ACQUIRED, REJECTED, etc.)
```

## Configuration

- **Without `OPENAI_API_KEY`**: Runs in mock mode, saves deals as drafts
- **`APIFY_API_TOKEN`**: Required only for Flippa import
- **Flippa workflow**: Manual trigger via CLI or service call; processes listings as batch to pipeline

## Deal Concepts

- `status` — Deal lifecycle state
- `score` — Overall rating (0–100)
- `confidence` — Confidence in score
- `decision` — BUY / WATCH / IGNORE
- `missing_info`, `questions_for_seller` — Due diligence notes

## Note

MVP stage: Focus on working pipeline, data structure, and core scoring logic.
