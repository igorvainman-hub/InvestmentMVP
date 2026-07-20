from agents.schemas import CollectorResponse
from agents.sources.flippa_normalizer import COLLECTOR_FIELDS, normalize_flippa_listing


def test_collector_response_accepts_new_fields():
    payload = {
        "source": "Flippa",
        "source_id": "123",
        "name": "Test Asset",
        "url": "https://example.com",
        "type": "SaaS",
        "description": "A useful product",
        "monetization_model": "subscription",
        "target_users": "founders",
        "price": 1000,
        "monthly_revenue": 250,
        "monthly_profit": 150,
        "profit_margin": 60,
        "traffic": 5000,
        "organic_traffic": 3000,
        "site_age": "3 years",
        "verified_revenue": True,
        "verified_traffic": True,
    }

    parsed = CollectorResponse.parse_obj(payload)

    assert parsed.source == "Flippa"
    assert parsed.source_id == "123"
    assert parsed.monthly_revenue == 250
    assert parsed.verified_revenue is True


def test_flippa_normalizer_uses_new_collector_fields():
    item = {
        "property_name": "Example Asset",
        "listing_url": "https://example.com/listing",
        "price": "$1200",
        "revenue_average": "$250",
        "uniques_per_month": "5000",
        "monetization": "subscription",
        "property_type": "saas",
    }

    normalized = normalize_flippa_listing(item)

    assert set(COLLECTOR_FIELDS) == {
        "source",
        "source_id",
        "name",
        "url",
        "type",
        "description",
        "monetization_model",
        "target_users",
        "price",
        "monthly_revenue",
        "monthly_profit",
        "profit_margin",
        "traffic",
        "organic_traffic",
        "site_age",
        "verified_revenue",
        "verified_traffic",
    }
    assert set(normalized.keys()) == set(COLLECTOR_FIELDS)
    assert normalized["name"] == "Example Asset"
    assert normalized["price"] == 1200.0
    assert normalized["monthly_revenue"] == 250.0
