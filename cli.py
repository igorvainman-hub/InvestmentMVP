"""
Investment OS — CLI (MVP)

Usage:
    python cli.py add                             # interactively add a deal via manual fields
    python cli.py notes                           # paste raw messy notes, let Collector structure it
    python cli.py list                            # list all deals sorted by score
    python cli.py show <deal_id>                  # show full detail of one deal
    python cli.py rerun <deal_id>                 # re-run analysis/scoring on existing deal
    python cli.py status <deal_id> <NEW_STATUS>   # e.g. WATCHLIST / ACQUIRED / REJECTED
"""

import sys
from pipeline import InvestmentOSPipeline


def print_deal_summary(deal):
    print(f"\n[{deal.status}] {deal.decision or '?'} score={deal.score} "
          f"conf={deal.confidence}%  {deal.name or '(no name)'}  ({deal.id})")
    print(f"  url: {deal.url}  source: {deal.source}")
    if deal.score_breakdown:
        print(f"  breakdown: {deal.score_breakdown}")
    if deal.missing_info:
        print(f"  missing: {', '.join(deal.missing_info[:3])}{' ...' if len(deal.missing_info) > 3 else ''}")


def print_deal_debug(deal):
    print(f"id={deal.id} status={deal.status} decision={deal.decision or '-'}")
    print(f"score={deal.score} confidence={deal.confidence}%")
    if deal.history:
        last_event = deal.history[-1]
        print(f"last_event={last_event.get('action')} :: {last_event.get('detail')}")
    if deal.missing_info:
        print(f"missing_info={deal.missing_info[:3]}")
    if deal.history:
        print("history:")
        for item in deal.history[-5:]:
            print(f"  - {item.get('actor')} | {item.get('action')} | {item.get('detail')}")


def print_pipeline_result(pipeline, deal):
    if pipeline.llm.mock and deal.status == "COLLECTED":
        print(
            "\nSaved as a draft. Set OPENAI_API_KEY, then run "
            f"python cli.py rerun {deal.id} to analyze it."
        )
    print_deal_debug(deal)


def cmd_add(pipeline):
    print("Enter deal fields (leave blank if unknown):")
    name = input("name: ").strip()
    url = input("url: ").strip()
    dtype = input("type (SaaS/site/extension/API/other): ").strip()
    price = input("price ($): ").strip()
    monthly_revenue = input("monthly revenue ($): ").strip()
    description = input("description: ").strip()
    source = input("source (Acquire/Flippa/GitHub/Reddit/Twitter/Manual/other) [Manual]: ").strip() or "Manual"

    fields = {
        "name": name,
        "url": url,
        "type": dtype,
        "description": description,
    }
    if price:
        fields["price"] = float(price)
    if monthly_revenue:
        fields["monthly_revenue"] = float(monthly_revenue)

    print("\nRunning pipeline (Collector -> Analyzer -> Growth -> Scoring -> [Due Diligence])...")
    deal = pipeline.run_from_manual_fields(source=source, **fields)
    print_pipeline_result(pipeline, deal)


def cmd_notes(pipeline):
    print("Paste raw notes about the deal (end with an empty line):")
    lines = []
    while True:
        line = input()
        if line == "":
            break
        lines.append(line)
    raw_notes = "\n".join(lines)
    source = input("source (Acquire/Flippa/GitHub/Reddit/Twitter/Manual/other) [Manual]: ").strip() or "Manual"

    print("\nRunning pipeline (Collector -> Analyzer -> Growth -> Scoring -> [Due Diligence])...")
    deal = pipeline.run_from_notes(raw_notes, source=source)
    print_pipeline_result(pipeline, deal)


def cmd_list(pipeline):
    deals = pipeline.store.sorted_by_score()
    if not deals:
        print("No deals stored yet.")
        return
    for deal in deals:
        print_deal_summary(deal)


def cmd_show(pipeline, deal_id):
    deal = pipeline.store.load(deal_id)
    if deal is None:
        print(f"Deal {deal_id} not found.")
        return
    print_deal_debug(deal)


def cmd_rerun(pipeline, deal_id):
    deal = pipeline.rerun_analysis(deal_id)
    print_deal_debug(deal)


def cmd_status(pipeline, deal_id, new_status):
    deal = pipeline.set_status(deal_id, new_status, actor="user")
    print_deal_summary(deal)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    pipeline = InvestmentOSPipeline()
    command = sys.argv[1]

    if command == "add":
        cmd_add(pipeline)
    elif command == "notes":
        cmd_notes(pipeline)
    elif command == "list":
        cmd_list(pipeline)
    elif command == "show" and len(sys.argv) > 2:
        cmd_show(pipeline, sys.argv[2])
    elif command == "rerun" and len(sys.argv) > 2:
        cmd_rerun(pipeline, sys.argv[2])
    elif command == "status" and len(sys.argv) > 3:
        cmd_status(pipeline, sys.argv[2], sys.argv[3])
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
