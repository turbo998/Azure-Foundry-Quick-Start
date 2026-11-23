import sys
import unittest
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import verify_foundry_estimated_cost as verifier


class VerifyFoundryEstimatedCostTests(unittest.TestCase):
    def test_validate_resource_id_accepts_valid_arm_path(self):
        rid = (
            "/subscriptions/00000000-0000-0000-0000-000000000000"
            "/resourceGroups/rg-demo/providers/Microsoft.CognitiveServices/accounts/foundry-demo/"
        )
        self.assertEqual(verifier.validate_resource_id(rid), rid.rstrip("/"))
        self.assertEqual(
            verifier.parse_subscription(rid),
            "00000000-0000-0000-0000-000000000000",
        )

    def test_validate_resource_id_rejects_non_cognitive_or_traversal(self):
        for bad in (
            "https://management.azure.com/subscriptions/0000/resourceGroups/rg",
            "/subscriptions/not-guid/resourceGroups/rg/providers/Microsoft.Storage/storageAccounts/sa",
            "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/rg/providers/Microsoft.CognitiveServices/accounts/a/projects/p",
        ):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                verifier.validate_resource_id(bad)

    def test_resolve_inference_target_distinguishes_account_vs_project_endpoint(self):
        acc_url, acc_aud, acc_extra = verifier.resolve_inference_target(
            "https://example-account.cognitiveservices.azure.com/",
            "gpt-4.1-mini",
        )
        self.assertEqual(
            acc_url,
            "https://example-account.cognitiveservices.azure.com/openai/deployments/gpt-4.1-mini/chat/completions?api-version=2025-01-01-preview",
        )
        self.assertEqual(acc_aud, "https://cognitiveservices.azure.com/")
        self.assertEqual(acc_extra, {})

        proj_url, proj_aud, proj_extra = verifier.resolve_inference_target(
            "https://example-account.services.ai.azure.com/api/projects/proj-alpha",
            "gpt-5.4-mini",
        )
        self.assertEqual(
            proj_url,
            "https://example-account.services.ai.azure.com/api/projects/proj-alpha/openai/v1/chat/completions",
        )
        self.assertEqual(proj_aud, "https://ai.azure.com")
        self.assertEqual(proj_extra, {"model": "gpt-5.4-mini"})

    def test_resolve_inference_target_rejects_insecure_or_secret_urls(self):
        for bad in (
            "http://example-account.cognitiveservices.azure.com",
            "https://user:secret@example-account.cognitiveservices.azure.com",
            "https://example-account.cognitiveservices.azure.com?api-key=secret",
        ):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                verifier.resolve_inference_target(bad, "gpt-4.1")

    def test_separate_metric_queries_avoid_project_id_on_token_metrics(self):
        cost_qs, token_qs = verifier.build_separate_metric_queries(
            "2026-11-16T00:00:00Z/2026-11-23T00:00:00Z"
        )
        cost_params = dict(urllib.parse.parse_qsl(cost_qs))
        token_params = dict(urllib.parse.parse_qsl(token_qs))

        self.assertEqual(cost_params["metricnames"], "FoundryModelEstimatedCost")
        self.assertIn("ProjectId eq '*'", cost_params["$filter"])
        self.assertEqual(token_params["metricnames"], "ModelRequests,InputTokens,OutputTokens")
        self.assertNotIn("ProjectId", token_params["$filter"])

    def test_calculate_expected_costs_reproduces_empirical_kv_cache_variance(self):
        # Empirical gpt-4.1-mini 5-call cache-hit scenario (55.1% cached):
        # 14,640 prompt tokens (6,576 uncached + 8,064 cached), 52 output tokens
        # Retail: $0.40/1M uncached, $0.10/1M cached, $1.60/1M output
        cache_aware, naive_diy, over_pct = verifier.calculate_expected_costs(
            prompt_tokens=14640,
            cached_tokens=8064,
            completion_tokens=52,
            in_rate=0.40,
            cached_in_rate=0.10,
            out_rate=1.60,
        )
        self.assertAlmostEqual(cache_aware, 0.00352000, places=8)
        self.assertAlmostEqual(naive_diy, 0.00593920, places=8)
        self.assertAlmostEqual(over_pct, 68.7272727, places=4)

    def test_extract_metadata_map_normalizes_azure_monitor_dimension_casing(self):
        ts = {
            "metadatavalues": [
                {"name": {"value": "ModelDeploymentName"}, "value": "gpt-5.4"},
                {"name": {"value": "projectid"}, "value": "N/A"},
            ]
        }
        meta = verifier.extract_metadata_map(ts)
        self.assertEqual(meta["modeldeploymentname"], "gpt-5.4")
        self.assertEqual(meta["projectid"], "N/A")


if __name__ == "__main__":
    unittest.main()
