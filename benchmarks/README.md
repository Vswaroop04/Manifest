# Provider Benchmarks

Since Geo Coding and Routing is the main core of the application I have created a small project to measures geocoding and routing providers for latency (p50/p90/p95/p99),
distance accuracy (km error from ground truth), and ELD-app suitability.

## Setup

```bash
cd benchmarks
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# fill in API keys in .env
```

## Run

```bash
# Run everything
python run_all.py

# Geocoding only (works with no API keys — runs Nominatim + Photon)
python run_all.py --geocoding-only

# Routing only (needs ORS_API_KEY for truck profile)
python run_all.py --routing-only
```

JSON results are written to `results/` with a timestamp.
Baseline results are committed at `results/baseline_geocoding.json` and `results/baseline_routing.json`.

## Metrics

- **Latency**: mean, stdev, p50, p90, p95, p99, min, max (all in ms)
- **Distance error**: haversine km from known ground-truth coordinates
  — mean, p50, p90, p95, p99, max
- **Relative error %**: `|measured - expected| / expected × 100`
  — used for routing distance accuracy
- **Success rate**: % of calls that returned a valid result

## Final Decisions

After running the full benchmark suite across 4 geocoding providers and 2 routing providers, the following were selected for the ELD app. See [RESULTS.md](./RESULTS.md) for the full analysis and reasoning.

| Layer | Primary | Backup | Ruled out |
|-------|---------|--------|-----------|
| Geocoding | Photon (Komoot) | Nominatim (OSM) | ORS (zip failure), LocationIQ (3s tail latency and 1 catastrophic failure) |
| Routing | ORS HGV | OSRM (car, fallback only) | HERE Maps, TomTom (credit card required) |
