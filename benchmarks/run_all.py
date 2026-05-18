"""
Master benchmark runner — runs geocoding and routing benchmarks sequentially.

Usage:
    cd benchmarks
    python run_all.py                    # run everything
    python run_all.py --geocoding-only
    python run_all.py --routing-only
"""
import sys
import argparse
from rich.console import Console

console = Console()


def main():
    parser = argparse.ArgumentParser(description="Run provider benchmarks")
    parser.add_argument("--geocoding-only", action="store_true")
    parser.add_argument("--routing-only", action="store_true")
    args = parser.parse_args()

    run_geocoding = not args.routing_only
    run_routing = not args.geocoding_only

    console.rule("[bold magenta]Spotter Labs — Provider Benchmark Suite[/bold magenta]")
    console.print()

    if run_geocoding:
        console.rule("[blue]GEOCODING[/blue]")
        from geocoding.benchmark import main as geo_main
        geo_main()
        console.print()

    if run_routing:
        console.rule("[blue]ROUTING[/blue]")
        from routing.benchmark import main as route_main
        route_main()
        console.print()

    console.rule("[bold magenta]Done[/bold magenta]")
    console.print("[dim]Full results saved to benchmarks/results/[/dim]")


if __name__ == "__main__":
    # must run from benchmarks/ directory so relative imports resolve
    sys.path.insert(0, ".")
    main()
