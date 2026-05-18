"""
Routing provider benchmark.

Measures latency, distance accuracy vs known ground truth,
truck profile support, geometry availability, and turn-by-turn quality.
"""
import json
import sys
import time
import statistics
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich import box

sys.path.insert(0, str(Path(__file__).parent.parent))

from routing.providers import OpenRouteServiceRouter, OSRMRouter
from routing.providers.base import BaseRoutingProvider, RouteResult
from config import ROUTING_TEST_CASES, BENCHMARK_RUNS, RATE_LIMIT_DELAY, ORS_API_KEY
from stats import latency_stats, error_stats, relative_error

console = Console()


def run_provider(provider: BaseRoutingProvider, runs: int) -> dict[str, list[RouteResult]]:
    results: dict[str, list[RouteResult]] = {}
    for tc in ROUTING_TEST_CASES:
        tc_results = []
        coords = [tc["start"]]
        if "waypoint" in tc:
            coords.append(tc["waypoint"])
        coords.append(tc["end"])

        for _ in range(runs):
            result = provider.route(coords, truck_profile=provider.supports_truck)
            tc_results.append(result)
            time.sleep(RATE_LIMIT_DELAY)

        results[tc["id"]] = tc_results
    return results


def compute_stats(results: list[RouteResult], test_case: dict) -> dict:
    successful = [r for r in results if r.success]
    latencies = [r.latency_ms for r in results]
    success_rate = len(successful) / len(results) * 100

    distances = [r.distance_miles for r in successful if r.distance_miles is not None]
    rel_errors = [
        relative_error(r.distance_miles, test_case["expected_miles"])
        for r in successful
        if r.distance_miles is not None
    ]

    return {
        "success_rate_pct": round(success_rate, 1),
        "latency": latency_stats(latencies),
        "distance_miles_mean": round(statistics.mean(distances), 1) if distances else None,
        "relative_error_pct": error_stats(rel_errors),
        "within_tolerance": (
            statistics.mean(rel_errors) <= test_case["tolerance_pct"]
            if rel_errors else False
        ),
        "has_geometry": successful[0].has_geometry if successful else False,
        "has_turn_by_turn": successful[0].has_turn_by_turn if successful else False,
        "truck_profile": successful[0].truck_profile if successful else False,
    }


def _fmt(val, unit="", na="n/a") -> str:
    return f"{val}{unit}" if val is not None else na


def print_results_table(all_stats: dict):
    for tc in ROUTING_TEST_CASES:
        table = Table(
            title=f"[bold cyan]{tc['id']}[/bold cyan]  [yellow]{tc['label']}[/yellow]  (expected ~{tc['expected_miles']} mi)",
            box=box.ROUNDED,
            show_lines=True,
        )
        table.add_column("Provider", style="bold white", no_wrap=True)
        table.add_column("Success", justify="center")
        table.add_column("Lat p50", justify="right")
        table.add_column("Lat p90", justify="right")
        table.add_column("Lat p95", justify="right")
        table.add_column("Lat p99", justify="right")
        table.add_column("Dist (mi)", justify="right")
        table.add_column("RelErr mean", justify="right")
        table.add_column("RelErr p95", justify="right")
        table.add_column("In tol?", justify="center")
        table.add_column("Truck", justify="center")
        table.add_column("Geo", justify="center")
        table.add_column("Steps", justify="center")

        for provider_name, tc_stats in all_stats.items():
            s = tc_stats[tc["id"]]
            ok_color = "green" if s["success_rate_pct"] == 100 else "red"
            lat = s["latency"]
            err = s["relative_error_pct"]
            table.add_row(
                provider_name,
                f"[{ok_color}]{s['success_rate_pct']}%[/{ok_color}]",
                f"{lat['p50']} ms",
                f"{lat['p90']} ms",
                f"{lat['p95']} ms",
                f"{lat['p99']} ms",
                _fmt(s["distance_miles_mean"], " mi"),
                _fmt(err["mean"], "%"),
                _fmt(err["p95"], "%"),
                "[green]Yes[/green]" if s["within_tolerance"] else "[red]No[/red]",
                "[green]Yes[/green]" if s["truck_profile"] else "[red]No[/red]",
                "[green]Yes[/green]" if s["has_geometry"] else "[red]No[/red]",
                "[green]Yes[/green]" if s["has_turn_by_turn"] else "[red]No[/red]",
            )
        console.print(table)
        console.print()


def print_summary_table(all_stats: dict):
    table = Table(
        title="[bold green]Overall Routing Summary — Recommendation[/bold green]",
        box=box.DOUBLE_EDGE,
    )
    table.add_column("Provider", style="bold white")
    table.add_column("Lat p50 avg", justify="right")
    table.add_column("Lat p95 avg", justify="right")
    table.add_column("RelErr mean avg", justify="right")
    table.add_column("RelErr p95 avg", justify="right")
    table.add_column("All in tol?", justify="center")
    table.add_column("Truck", justify="center")
    table.add_column("Geometry", justify="center")
    table.add_column("Steps", justify="center")
    table.add_column("ELD pick?", justify="center")

    for provider_name, tc_stats in all_stats.items():
        p50s  = [s["latency"]["p50"] for s in tc_stats.values()]
        p95s  = [s["latency"]["p95"] for s in tc_stats.values()]
        means = [s["relative_error_pct"]["mean"] for s in tc_stats.values() if s["relative_error_pct"]["mean"] is not None]
        p95es = [s["relative_error_pct"]["p95"]  for s in tc_stats.values() if s["relative_error_pct"]["p95"]  is not None]
        all_in_tol = all(s["within_tolerance"] for s in tc_stats.values())
        truck = any(s["truck_profile"] for s in tc_stats.values())
        geo   = any(s["has_geometry"] for s in tc_stats.values())
        steps = any(s["has_turn_by_turn"] for s in tc_stats.values())
        recommended = truck and geo and all_in_tol

        table.add_row(
            provider_name,
            f"{sum(p50s)/len(p50s):.0f} ms",
            f"{sum(p95s)/len(p95s):.0f} ms",
            f"{sum(means)/len(means):.1f}%" if means else "n/a",
            f"{sum(p95es)/len(p95es):.1f}%" if p95es else "n/a",
            "[green]Yes[/green]" if all_in_tol else "[red]No[/red]",
            "[green]Yes[/green]" if truck else "[red]No[/red]",
            "[green]Yes[/green]" if geo else "[red]No[/red]",
            "[green]Yes[/green]" if steps else "[red]No[/red]",
            "[bold green]YES[/bold green]" if recommended else "[dim]No[/dim]",
        )
    console.print(table)


def save_results(all_stats: dict):
    out_dir = Path(__file__).parent.parent / "results"
    out_dir.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = out_dir / f"routing_{ts}.json"
    out_path.write_text(json.dumps({"run_at": ts, "results": all_stats}, indent=2))
    console.print(f"\n[dim]Results saved → {out_path}[/dim]")


def main():
    console.rule("[bold blue]Routing Provider Benchmark[/bold blue]")

    providers: list[BaseRoutingProvider] = [
        OSRMRouter(),
    ]

    if ORS_API_KEY:
        providers.insert(0, OpenRouteServiceRouter(ORS_API_KEY))
    else:
        console.print("[yellow]ORS_API_KEY not set — skipping OpenRouteService router[/yellow]\n")

    console.print(f"Providers : {[p.name for p in providers]}")
    console.print(f"Test cases: {len(ROUTING_TEST_CASES)}")
    console.print(f"Runs each : {BENCHMARK_RUNS}")
    console.print(f"Total calls: {len(providers) * len(ROUTING_TEST_CASES) * BENCHMARK_RUNS}\n")

    all_stats = {}
    for provider in providers:
        console.print(f"[cyan]Running {provider.name}...[/cyan]")
        raw = run_provider(provider, BENCHMARK_RUNS)
        stats = {
            tc["id"]: compute_stats(raw[tc["id"]], tc)
            for tc in ROUTING_TEST_CASES
        }
        all_stats[provider.name] = stats
        console.print(f"  [green]Done[/green]")

    console.print()
    print_results_table(all_stats)
    print_summary_table(all_stats)
    save_results(all_stats)


if __name__ == "__main__":
    main()
