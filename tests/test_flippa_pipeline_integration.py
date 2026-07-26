import os
import tempfile
import unittest
from unittest.mock import Mock, patch

from deal_model import DealObject
from pipeline import InvestmentOSPipeline
from agents.sources.flippa_service import FlippaService


class FlippaPipelineIntegrationTest(unittest.TestCase):
    def test_pipeline_can_run_from_existing_flippa_deal(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            pipeline = InvestmentOSPipeline(storage_dir=tmp_dir)

            with patch.object(pipeline.collector, "collect_manual", side_effect=AssertionError("collector should not be invoked")):
                with patch.object(pipeline.collector, "collect_from_notes", side_effect=AssertionError("collector should not be invoked")):
                    deal = DealObject(source="Flippa", name="Test Asset", url="https://example.com")

                    result = pipeline.run_from_deals(deal)

                    self.assertEqual(result.id, deal.id)
                    self.assertEqual(result.source, "Flippa")
                    self.assertEqual(result.name, "Test Asset")

    def test_pipeline_can_run_from_multiple_flippa_deals(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            pipeline = InvestmentOSPipeline(storage_dir=tmp_dir)
            deals = [
                DealObject(source="Flippa", name="Asset One", url="https://example.com/one"),
                DealObject(source="Flippa", name="Asset Two", url="https://example.com/two"),
            ]

            results = pipeline.run_from_deals(deals)

            self.assertEqual(len(results), 2)
            self.assertEqual([deal.name for deal in results], ["Asset One", "Asset Two"])
            self.assertEqual(len(os.listdir(os.path.join(tmp_dir, "deals"))), 2)

    def test_flippa_service_forwards_batch_to_pipeline(self):
        client = Mock()
        client.fetch_listings.return_value = [
            {"property_name": "Asset One", "listing_url": "https://example.com/one"},
            {"property_name": "Asset Two", "listing_url": "https://example.com/two"},
        ]
        archive = Mock()
        archive.save_batch.return_value = [
            DealObject(source="Flippa", name="Asset One", url="https://example.com/one"),
            DealObject(source="Flippa", name="Asset Two", url="https://example.com/two"),
        ]

        service = FlippaService(client=client, archive=archive)
        pipeline = Mock()
        pipeline.run_from_deals.return_value = ["done", "done"]

        results = service.fetch_and_process(pipeline=pipeline, limit=2)

        self.assertEqual(results, ["done", "done"])
        pipeline.run_from_deals.assert_called_once()
        self.assertEqual(len(pipeline.run_from_deals.call_args[0][0]), 2)


if __name__ == "__main__":
    unittest.main()
