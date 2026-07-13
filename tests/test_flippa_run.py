"""Quick test of FlippaService with maxItems=10."""

from agents.sources.flippa_service import FlippaService


def main():
    print("Testing FlippaService with maxItems=10...\n")
    
    service = FlippaService()
    
    try:
        # Fetch up to 10 listings
        results = service.fetch_and_archive(maxItems=10)
        
        print(f"✓ Success! Fetched and archived {len(results)} listings:\n")
        for i, deal in enumerate(results, 1):
            print(f"  {i}. {deal.name or '(no name)'}")
            print(f"     URL: {deal.url}")
            print(f"     Price: ${deal.price_usd or 'N/A'}")
            print()
            
    except ValueError as e:
        print(f"✗ Error: {e}")
        print("  (This is expected if APIFY_API_TOKEN is not set)\n")
    except Exception as e:
        print(f"✗ Unexpected error: {e}\n")


if __name__ == "__main__":
    main()
