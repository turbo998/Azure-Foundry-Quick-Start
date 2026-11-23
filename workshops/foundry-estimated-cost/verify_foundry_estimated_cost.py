#!/usr/bin/env python3
"""
Partner Self-Verification CLI for Azure Monitor `FoundryModelEstimatedCost` (Preview)

Zero-dependency (Python 3.10+ stdlib + Azure CLI `az login`) verification tool for
Microsoft Foundry (`AIServices`) and Azure OpenAI (`OpenAI`) resources:

1. Control-Plane Readiness: Verifies `FoundryModelEstimatedCost` in
   `Microsoft.Insights/metricDefinitions` (category, `Total`-only aggregation,
   `PT1M`..`P1D` timeGrains, `P93D` retention, and `ProjectId` / `ModelDeploymentName` /
   `ModelName` / `ModelVersion` / `Region` dimensions).
2. Historical Comparison (`--days`, default 7): Queries `FoundryModelEstimatedCost`
   separately from `ModelRequests,InputTokens,OutputTokens` to avoid the Azure Monitor
   `HTTP 400 BadRequest` dimension-mismatch error (`InputTokens` lacks `ProjectId`).
3. Optional 1-Call Live E2E Probe (`--endpoint` + `--deployment`): Supports both
   Account endpoints (`https://<account>.cognitiveservices.azure.com`, Entra audience
   `https://cognitiveservices.azure.com/`) and Foundry Project endpoints
   (`https://<account>.services.ai.azure.com/api/projects/<project>`, Entra audience
   `https://ai.azure.com`), polls `PT1M` buckets until ingestion (~90-180s), and
   compares reported USD against cache-aware retail token math vs naive DIY token math.

Usage:
  # 1. Control-plane & 7-day historical audit (zero inference cost):
  python workshops/foundry-estimated-cost/verify_foundry_estimated_cost.py \
    --resource-id "/subscriptions/<sub-id>/resourceGroups/<rg>/providers/Microsoft.CognitiveServices/accounts/<account>" \
    --days 7

  # 2. With 1-call live E2E probe & retail rate verification:
  python workshops/foundry-estimated-cost/verify_foundry_estimated_cost.py \
    --resource-id "/subscriptions/<sub-id>/resourceGroups/<rg>/providers/Microsoft.CognitiveServices/accounts/<account>" \
    --endpoint "https://<account>.cognitiveservices.azure.com" \
    --deployment "<chat-deployment-name>" \
    --input-price-per-1m 0.40 --cached-input-price-per-1m 0.10 --output-price-per-1m 1.60
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import datetime, timedelta, timezone

RESOURCE_ID_RE = re.compile(
    r"^/subscriptions/[0-9a-fA-F-]+/resourceGroups/[^/]+/providers/"
    r"Microsoft\.CognitiveServices/accounts/[^/]+$",
    re.IGNORECASE,
)
DEPLOYMENT_RE = re.compile(r"^[A-Za-z0-9._-]+$")


def validate_resource_id(resource_id: str) -> str:
    cleaned = resource_id.strip().rstrip("/")
    if not RESOURCE_ID_RE.match(cleaned):
        raise ValueError(
            "Invalid --resource-id. Expected '/subscriptions/<sub-id>/resourceGroups/<rg>/"
            "providers/Microsoft.CognitiveServices/accounts/<account>'."
        )
    return cleaned


def validate_deployment(deployment: str) -> str:
    cleaned = deployment.strip()
    if not DEPLOYMENT_RE.match(cleaned):
        raise ValueError(
            "Invalid --deployment name. Only alphanumeric characters, '.', '_', and '-' are allowed."
        )
    return cleaned


def resolve_inference_target(endpoint: str, deployment: str, api_version: str = "2025-01-01-preview") -> tuple[str, str, dict]:
    """Return (chat_completions_url, entra_audience, extra_payload_fields) for Account vs Project endpoint."""
    parsed = urllib.parse.urlsplit(endpoint.strip())
    if parsed.scheme.lower() != "https" or not parsed.hostname:
        raise ValueError("Invalid --endpoint: must be an https:// URL.")
    if parsed.username or parsed.password or parsed.query:
        raise ValueError("Invalid --endpoint: do not embed credentials or query strings in endpoint URL.")

    base_path = parsed.path.rstrip("/")
    base_url = f"https://{parsed.netloc}{base_path}"
    if "/api/projects/" in base_path.lower():
        url = f"{base_url}/openai/v1/chat/completions"
        return url, "https://ai.azure.com", {"model": deployment}

    safe_dep = urllib.parse.quote(deployment, safe="")
    safe_ver = urllib.parse.quote(api_version, safe="")
    url = f"{base_url}/openai/deployments/{safe_dep}/chat/completions?api-version={safe_ver}"
    return url, "https://cognitiveservices.azure.com/", {}


def calculate_expected_costs(
    prompt_tokens: int,
    cached_tokens: int,
    completion_tokens: int,
    in_rate: float,
    cached_in_rate: float | None,
    out_rate: float,
) -> tuple[float, float, float]:
    """Return (cache_aware_usd, naive_diy_usd, naive_overestimate_pct)."""
    if prompt_tokens < 0 or cached_tokens < 0 or completion_tokens < 0:
        raise ValueError("Token counts must be non-negative.")
    if cached_tokens > prompt_tokens:
        raise ValueError("cached_tokens cannot exceed prompt_tokens.")
    uncached_tokens = prompt_tokens - cached_tokens
    effective_cached_rate = cached_in_rate if cached_in_rate is not None else in_rate
    cache_aware_usd = (
        uncached_tokens * in_rate
        + cached_tokens * effective_cached_rate
        + completion_tokens * out_rate
    ) / 1_000_000.0
    naive_diy_usd = (prompt_tokens * in_rate + completion_tokens * out_rate) / 1_000_000.0
    overestimate_pct = (
        ((naive_diy_usd - cache_aware_usd) / cache_aware_usd) * 100.0
        if cache_aware_usd > 0
        else 0.0
    )
    return cache_aware_usd, naive_diy_usd, overestimate_pct


def build_separate_metric_queries(timespan: str, interval: str = "P1D") -> tuple[str, str]:
    """Build separate query strings for FoundryModelEstimatedCost vs Token metrics to prevent HTTP 400."""
    cost_qs = urllib.parse.urlencode(
        {
            "api-version": "2024-02-01",
            "metricnames": "FoundryModelEstimatedCost",
            "timespan": timespan,
            "interval": interval,
            "aggregation": "Total",
            "$filter": (
                "ProjectId eq '*' and ModelDeploymentName eq '*' "
                "and ModelName eq '*' and ModelVersion eq '*'"
            ),
        }
    )
    token_qs = urllib.parse.urlencode(
        {
            "api-version": "2024-02-01",
            "metricnames": "ModelRequests,InputTokens,OutputTokens",
            "timespan": timespan,
            "interval": interval,
            "aggregation": "Total",
            "$filter": "ModelDeploymentName eq '*' and ModelName eq '*'",
        }
    )
    return cost_qs, token_qs


def extract_metadata_map(timeseries_item: dict) -> dict[str, str]:
    return {
        mv.get("name", {}).get("value", "").lower(): mv.get("value", "")
        for mv in timeseries_item.get("metadatavalues", [])
        if mv.get("name", {}).get("value")
    }


def get_az_token(resource: str, subscription: str | None = None) -> str:
    az_bin = shutil.which("az.cmd") or shutil.which("az")
    if not az_bin:
        raise RuntimeError("Azure CLI (`az`) not found in PATH. Install Azure CLI and run `az login` first.")
    cmd = [az_bin, "account", "get-access-token", "--resource", resource, "-o", "json"]
    if subscription:
        cmd.extend(["--subscription", subscription])
    res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", check=True)
    return json.loads(res.stdout)["accessToken"]


def http_json(url: str, token: str, payload: dict | None = None, timeout: int = 30) -> dict:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(
        url,
        data=data,
        method="POST" if data is not None else "GET",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def parse_subscription(resource_id: str) -> str | None:
    parts = resource_id.strip("/").split("/")
    if len(parts) >= 2 and parts[0].lower() == "subscriptions":
        return parts[1]
    return None


def check_metric_definition(resource_id: str, arm_token: str) -> bool:
    url = f"https://management.azure.com{resource_id}/providers/Microsoft.Insights/metricDefinitions?api-version=2024-02-01"
    defs = http_json(url, arm_token).get("value", [])
    for d in defs:
        if d.get("name", {}).get("value") == "FoundryModelEstimatedCost":
            dims = [x["value"] for x in d.get("dimensions", [])]
            avail = [
                f"{x.get('timeGrain')} (retention={x.get('retention')})"
                for x in d.get("metricAvailabilities", [])
            ]
            print("[PASS] Metric Definition Found:")
            print(f"  Namespace   : {d.get('namespace')}")
            print(f"  Name        : {d['name']['value']} ({d['name'].get('localizedValue')})")
            print(f"  Category    : {d.get('category')} | Unit: {d.get('unit')}")
            print(
                f"  Aggregation : {d.get('supportedAggregationTypes')} "
                f"(Primary: {d.get('primaryAggregationType')})"
            )
            print(f"  Dimensions  : {dims}")
            print(f"  TimeGrains  : {avail}")
            return True
    print(
        "[FAIL] FoundryModelEstimatedCost is NOT registered on this resource "
        "(expected on AIServices or OpenAI kinds; not registered on SpeechServices)."
    )
    return False


def query_historical(resource_id: str, arm_token: str, days: int) -> None:
    now = datetime.now(timezone.utc)
    timespan = (
        f"{(now - timedelta(days=days)).strftime('%Y-%m-%dT%H:%M:%SZ')}/"
        f"{now.strftime('%Y-%m-%dT%H:%M:%SZ')}"
    )
    print(f"\n=== Historical Summary (Last {days} days: {timespan}) ===")
    cost_qs, token_qs = build_separate_metric_queries(timespan, interval="P1D")

    rc = http_json(
        f"https://management.azure.com{resource_id}/providers/Microsoft.Insights/metrics?{cost_qs}",
        arm_token,
    )
    found_cost = False
    for m in rc.get("value", []):
        for ts in m.get("timeseries", []):
            pts = [pt.get("total") or 0.0 for pt in ts.get("data", []) if (pt.get("total") or 0.0) > 0]
            if pts:
                found_cost = True
                meta = extract_metadata_map(ts)
                print(
                    f"  [FoundryModelEstimatedCost] ${sum(pts):.8f} USD | "
                    f"deployment={meta.get('modeldeploymentname')} model={meta.get('modelname')} "
                    f"v={meta.get('modelversion')} ProjectId={meta.get('projectid')}"
                )
    if not found_cost:
        print("  [FoundryModelEstimatedCost] No non-zero series in window.")

    rt = http_json(
        f"https://management.azure.com{resource_id}/providers/Microsoft.Insights/metrics?{token_qs}",
        arm_token,
    )
    for m in rt.get("value", []):
        mname = m["name"]["value"]
        for ts in m.get("timeseries", []):
            pts = [pt.get("total") or 0.0 for pt in ts.get("data", []) if (pt.get("total") or 0.0) > 0]
            if pts:
                meta = extract_metadata_map(ts)
                print(
                    f"  [{mname}] {sum(pts):,.0f} | "
                    f"deployment={meta.get('modeldeploymentname')} ({meta.get('modelname')})"
                )


def run_live_probe(
    resource_id: str,
    arm_token: str,
    endpoint: str,
    deployment: str,
    subscription: str | None,
    in_rate: float | None,
    cached_in_rate: float | None,
    out_rate: float | None,
    poll_interval_seconds: int = 20,
    max_attempts: int = 12,
) -> None:
    chat_url, audience, extra_fields = resolve_inference_target(endpoint, deployment)
    inference_token = get_az_token(audience, subscription)

    print(f"\n=== Live E2E Probe on deployment '{deployment}' (audience: {audience}) ===")
    t_before = datetime.now(timezone.utc) - timedelta(minutes=1)
    prompt = f"TraceNonce={uuid.uuid4()}. Explain Azure Monitor PT1M metric aggregation in one concise sentence."
    payload = {
        **extra_fields,
        "messages": [{"role": "user", "content": prompt}],
        "max_completion_tokens": 50,
    }

    t0 = time.time()
    resp = http_json(chat_url, inference_token, payload)
    usage = resp.get("usage", {})
    prompt_tokens = int(usage.get("prompt_tokens", 0))
    cached_tokens = int((usage.get("prompt_tokens_details") or {}).get("cached_tokens", 0))
    uncached_tokens = prompt_tokens - cached_tokens
    completion_tokens = int(usage.get("completion_tokens", 0))
    print(
        f"  Inference HTTP 200 in {(time.time() - t0) * 1000:.0f} ms | "
        f"prompt={prompt_tokens} (uncached={uncached_tokens}, cached={cached_tokens}), "
        f"completion={completion_tokens}"
    )

    expected_usd: float | None = None
    if in_rate is not None and out_rate is not None:
        expected_usd, naive_usd, over_pct = calculate_expected_costs(
            prompt_tokens, cached_tokens, completion_tokens, in_rate, cached_in_rate, out_rate
        )
        print(f"  Expected Cache-Aware Retail Cost : ${expected_usd:.8f} USD")
        if cached_tokens > 0 and cached_in_rate is not None:
            print(
                f"  Naive DIY Token Formula Cost     : ${naive_usd:.8f} USD "
                f"(+{over_pct:.2f}% overestimate from unsplit cached tokens)"
            )

    print("  Polling Azure Monitor PT1M FoundryModelEstimatedCost (typical lag: 90-180s)...")
    for attempt in range(1, max_attempts + 1):
        time.sleep(poll_interval_seconds)
        now = datetime.now(timezone.utc)
        timespan = f"{t_before.strftime('%Y-%m-%dT%H:%M:%SZ')}/{now.strftime('%Y-%m-%dT%H:%M:%SZ')}"
        p = urllib.parse.urlencode(
            {
                "api-version": "2024-02-01",
                "metricnames": "FoundryModelEstimatedCost",
                "timespan": timespan,
                "interval": "PT1M",
                "aggregation": "Total",
                "$filter": f"ModelDeploymentName eq '{deployment}' and ProjectId eq '*'",
            }
        )
        rc = http_json(
            f"https://management.azure.com{resource_id}/providers/Microsoft.Insights/metrics?{p}",
            arm_token,
        )
        for m in rc.get("value", []):
            for ts in m.get("timeseries", []):
                pts = [
                    (pt["timeStamp"], float(pt.get("total") or 0.0))
                    for pt in ts.get("data", [])
                    if (pt.get("total") or 0.0) > 0
                ]
                if pts:
                    total_usd = sum(v for _, v in pts)
                    lag_s = time.time() - t0
                    meta = extract_metadata_map(ts)
                    variance_note = ""
                    if expected_usd is not None and expected_usd > 0:
                        rel_err = abs(total_usd - expected_usd) / expected_usd * 100.0
                        variance_note = f" | error={rel_err:.4f}%"
                    print(
                        f"  [INGESTED in {lag_s:.0f}s] Reported FoundryModelEstimatedCost = "
                        f"${total_usd:.8f} USD{variance_note} | "
                        f"ProjectId={meta.get('projectid')} | points={pts}"
                    )
                    return
        print(f"    Attempt {attempt}/{max_attempts}: waiting for PT1M metric bucket...")
    print(
        "  [WARN] No non-zero FoundryModelEstimatedCost observed within polling window "
        "(verify whether this model modality is supported in Preview; Embeddings and Image Generation currently emit $0)."
    )


def main() -> None:
    ap = argparse.ArgumentParser(description="Verify Azure Monitor FoundryModelEstimatedCost (Preview)")
    ap.add_argument(
        "--resource-id",
        required=True,
        help="Full ARM resource ID of Microsoft.CognitiveServices/accounts/<name>",
    )
    ap.add_argument("--days", type=int, default=7, help="Historical lookback days (default: 7)")
    ap.add_argument(
        "--endpoint",
        help="Optional Account or Foundry Project https:// endpoint for 1-call live E2E probe",
    )
    ap.add_argument("--deployment", help="Optional chat deployment name for 1-call live E2E probe")
    ap.add_argument("--input-price-per-1m", type=float, help="Optional uncached input USD per 1M tokens")
    ap.add_argument("--cached-input-price-per-1m", type=float, help="Optional cached input USD per 1M tokens")
    ap.add_argument("--output-price-per-1m", type=float, help="Optional output USD per 1M tokens")
    args = ap.parse_args()

    resource_id = validate_resource_id(args.resource_id)
    sub = parse_subscription(resource_id)
    arm_token = get_az_token("https://management.azure.com/", sub)
    if not check_metric_definition(resource_id, arm_token):
        return
    if args.days > 0:
        query_historical(resource_id, arm_token, args.days)

    if args.endpoint and args.deployment:
        deployment = validate_deployment(args.deployment)
        run_live_probe(
            resource_id,
            arm_token,
            args.endpoint,
            deployment,
            sub,
            args.input_price_per_1m,
            args.cached_input_price_per_1m,
            args.output_price_per_1m,
        )


if __name__ == "__main__":
    main()
