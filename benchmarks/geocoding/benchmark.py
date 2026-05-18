"""
Geocoding provider benchmark.

Metrics per test case:
  - Latency: mean, stdev, p50, p90, p95, p99, min, max
  - Accuracy: distance error (km) from known ground-truth coords
    reported as mean, p50, p90, p95, p99
  - Success rate

Providers compared:
  - OpenRouteService (Pelias-based, needs key)
  - Nominatim (OSM, free, no key)
  - Photon by Komoot (OSM, free, no key)
  - LocationIQ structured API (needs key) — structured fields reduce
    freeform parse failures that cause large positional errors
"""
import json
import sys
import time
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich import box

sys.path.insert(0, str(Path(__file__).parent.parent))

from geocoding.providers import OpenRouteServiceGeocoder, NominatimGeocoder, PhotonGeocoder
from geocoding.providers.locationiq import LocationIQStructuredGeocoder
from geocoding.providers.base import BaseGeocodeProvider, GeocodeResult
from config import GEOCODING_TEST_CASES, BENCHMARK_RUNS, RATE_LIMIT_DELAY, ORS_API_KEY, LOCATIONIQ_API_KEY
from stats import latency_stats, error_stats, haversine_km

console = Console()


def run_provider(provider: BaseGeocodeProvider, runs: int) -> dict[str, list[GeocodeResult]]:
    results: dict[str, list[GeocodeResult]] = {}
    for tc in GEOCODING_TEST_CASES:
        tc_results = []
        for _ in range(runs):
            result = provider.geocode(tc["query"])
            tc_results.append(result)
            time.sleep(RATE_LIMIT_DELAY)
        results[tc["id"]] = tc_results
    return results


def compute_stats(results: list[GeocodeResult], test_case: dict) -> dict:
    successful = [r for r in results if r.success]
    success_rate = len(successful) / len(results) * 100

    latencies = [r.latency_ms for r in results]

    # Distance errors only when we have ground truth
    dist_errors_km: list[float] = []
    if test_case["expected_lat"] is not None:
        for r in successful:
            if r.lat is not None and r.lng is not None:
                err = haversine_km(r.lat, r.lng, test_case["expected_lat"], test_case["expected_lng"])
                dist_errors_km.append(err)

    return {
        "success_rate_pct": round(success_rate, 1),
        "latency": latency_stats(latencies),
        "distance_error_km": error_stats(dist_errors_km),
        "sample_label": successful[0].label[:60] if successful else "",
        "sample_confidence": round(successful[0].confidence, 3) if successful and successful[0].confidence is not None else None,
    }


def _fmt(val, unit="", na="n/a") -> str:
    return f"{val}{unit}" if val is not None else na


def print_latency_table(all_stats: dict):
    """One table showing latency percentiles across all providers × test cases."""
    table = Table(
        title="[bold cyan]Latency (ms) — all providers × test cases[/bold cyan]",
        box=box.ROUNDED, show_lines=True,
    )
    table.add_column("Provider", style="bold white", no_wrap=True)
    table.add_column("Test case")
    table.add_column("mean", justify="right")
    table.add_column("p50", justify="right")
    table.add_column("p90", justify="right")
    table.add_column("p95", justify="right")
    table.add_column("p99", justify="right")
    table.add_column("max", justify="right")
    table.add_column("stdev", justify="right")

    for provider_name, tc_stats in all_stats.items():
        first = True
        for tc in GEOCODING_TEST_CASES:
            s = tc_stats[tc["id"]]["latency"]
            table.add_row(
                provider_name if first else "",
                tc["id"],
                f"{s['mean']}",
                f"{s['p50']}",
                f"{s['p90']}",
                f"{s['p95']}",
                f"{s['p99']}",
                f"{s['max']}",
                f"{s['stdev']}",
            )
            first = False

    console.print(table)
    console.print()


def print_accuracy_table(all_stats: dict):
    """One table showing distance-error percentiles across all providers × test cases."""
    table = Table(
        title="[bold cyan]Distance Error (km from ground truth)[/bold cyan]",
        box=box.ROUNDED, show_lines=True,
    )
    table.add_column("Provider", style="bold white", no_wrap=True)
    table.add_column("Test case")
    table.add_column("mean", justify="right")
    table.add_column("p50", justify="right")
    table.add_column("p90", justify="right")
    table.add_column("p95", justify="right")
    table.add_column("p99", justify="right")
    table.add_column("max", justify="right")

    for provider_name, tc_stats in all_stats.items():
        first = True
        for tc in GEOCODING_TEST_CASES:
            if tc["expected_lat"] is None:
                continue  # skip ambiguous test cases
            s = tc_stats[tc["id"]]["distance_error_km"]
            table.add_row(
                provider_name if first else "",
                tc["id"],
                _fmt(s["mean"], " km"),
                _fmt(s["p50"],  " km"),
                _fmt(s["p90"],  " km"),
                _fmt(s["p95"],  " km"),
                _fmt(s["p99"],  " km"),
                _fmt(s["max"],  " km"),
            )
            first = False

    console.print(table)
    console.print()


def print_summary_table(all_stats: dict):
    table = Table(
        title="[bold green]Overall Geocoding Summary — Recommendation[/bold green]",
        box=box.DOUBLE_EDGE,
    )
    table.add_column("Provider", style="bold white")
    table.add_column("Avg Latency p50", justify="right")
    table.add_column("Avg Latency p95", justify="right")
    table.add_column("Avg Dist Err mean", justify="right")
    table.add_column("Avg Dist Err p95", justify="right")
    table.add_column("Success rate", justify="right")
    table.add_column("Key required", justify="center")
    table.add_column("Use for ELD?", justify="center")

    key_required = {
        "OpenRouteService": "[yellow]Yes (free)[/yellow]",
        "Nominatim (OSM)":  "[green]No[/green]",
        "Photon (Komoot)":  "[green]No[/green]",
        "LocationIQ (structured)": "[yellow]Yes (free)[/yellow]",
    }

    for provider_name, tc_stats in all_stats.items():
        latencies_p50 = [s["latency"]["p50"] for s in tc_stats.values()]
        latencies_p95 = [s["latency"]["p95"] for s in tc_stats.values()]
        errors_mean = [s["distance_error_km"]["mean"] for s in tc_stats.values() if s["distance_error_km"]["mean"] is not None]
        errors_p95  = [s["distance_error_km"]["p95"]  for s in tc_stats.values() if s["distance_error_km"]["p95"]  is not None]
        success_rates = [s["success_rate_pct"] for s in tc_stats.values()]

        avg_lat_p50 = sum(latencies_p50) / len(latencies_p50)
        avg_lat_p95 = sum(latencies_p95) / len(latencies_p95)
        avg_err_mean = sum(errors_mean) / len(errors_mean) if errors_mean else None
        avg_err_p95  = sum(errors_p95)  / len(errors_p95)  if errors_p95  else None
        avg_success  = sum(success_rates) / len(success_rates)

        # For an ELD app: want <500ms p95, <5km mean error, >95% success
        good = (
            avg_lat_p95 < 500
            and (avg_err_mean is None or avg_err_mean < 5)
            and avg_success >= 95
        )

        table.add_row(
            provider_name,
            f"{avg_lat_p50:.0f} ms",
            f"{avg_lat_p95:.0f} ms",
            _fmt(round(avg_err_mean, 2) if avg_err_mean else None, " km"),
            _fmt(round(avg_err_p95,  2) if avg_err_p95  else None, " km"),
            f"{avg_success:.1f}%",
            key_required.get(provider_name, "?"),
            "[bold green]YES[/bold green]" if good else "[dim]No[/dim]",
        )
    console.print(table)
    console.print()


def save_results(all_stats: dict):
    out_dir = Path(__file__).parent.parent / "results"
    out_dir.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = out_dir / f"geocoding_{ts}.json"
    out_path.write_text(json.dumps({"run_at": ts, "results": all_stats}, indent=2))
    console.print(f"[dim]Results saved → {out_path}[/dim]")


def main():
    console.rule("[bold blue]Geocoding Provider Benchmark[/bold blue]")

    providers: list[BaseGeocodeProvider] = [
        NominatimGeocoder(),
        PhotonGeocoder(),
    ]
    if ORS_API_KEY:
        providers.insert(0, OpenRouteServiceGeocoder(ORS_API_KEY))
    else:
        console.print("[yellow]ORS_API_KEY not set — skipping OpenRouteService[/yellow]")

    if LOCATIONIQ_API_KEY:
        providers.append(LocationIQStructuredGeocoder(LOCATIONIQ_API_KEY))
    else:
        console.print("[yellow]LOCATIONIQ_API_KEY not set — skipping LocationIQ[/yellow]")

    console.print(f"\nProviders  : {[p.name for p in providers]}")
    console.print(f"Test cases : {len(GEOCODING_TEST_CASES)}")
    console.print(f"Runs each  : {BENCHMARK_RUNS}")
    total = len(providers) * len(GEOCODING_TEST_CASES) * BENCHMARK_RUNS
    est_secs = total * RATE_LIMIT_DELAY
    console.print(f"Total calls: {total}  (~{est_secs:.0f}s with rate-limit delay)\n")

    all_stats: dict[str, dict] = {}
    for provider in providers:
        console.print(f"[cyan]Running {provider.name}...[/cyan]")
        raw = run_provider(provider, BENCHMARK_RUNS)
        all_stats[provider.name] = {
            tc["id"]: compute_stats(raw[tc["id"]], tc)
            for tc in GEOCODING_TEST_CASES
        }
        console.print(f"  [green]Done ✓[/green]")

    console.print()
    print_latency_table(all_stats)
    print_accuracy_table(all_stats)
    print_summary_table(all_stats)
    save_results(all_stats)


if __name__ == "__main__":
    main()
