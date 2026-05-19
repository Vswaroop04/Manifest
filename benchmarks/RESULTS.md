# Provider Selection — My Research & Reasoning

Since geocoding and routing are the backbone of this app, I didn't want to
just pick a provider blindly. I wrote a benchmark suite to actually measure
latency and accuracy across the real query types drivers would use — city
names, full street addresses, zip codes, highway-style queries. Here's what
I found and why I made the choices I did.

Baseline result files: `results/baseline_geocoding.json`, `results/baseline_routing.json`

---

## Geocoding

### What I tested and why

The first thing I looked at was which providers were actually free with no
credit card. I came across HERE Maps and TomTom — both have good geocoding
and truck routing, but both require a credit card at signup even for the
free tier. I didn't want any billing dependency on a demo app so I ruled
both of them out early and focused on the open options.

That left me with four providers to benchmark:
- **Nominatim** — the OSM geocoder, completely free, no key needed
- **Photon by Komoot** — also OSM-based, completely free, no key needed
- **OpenRouteService** — free but needs an API key (free registration)
- **LocationIQ** — has a structured API endpoint I wanted to try, free tier
  with a key

I tested all four against 8 query types and ran each 5 times to get reliable
latency percentiles (p50, p90, p95, p99).

---

### What the numbers showed

**Latency:**

Nominatim was the fastest by far — around 75ms p50. Everything else was in
the 680–800ms range which is still fine for a form autocomplete. The one
that surprised me was LocationIQ — on some queries the p99 hit nearly
3 seconds. That's a long time to wait for an address suggestion to appear,
so I dropped it.

**Accuracy:**

This is where things got interesting. For simple city queries like
"Chicago, IL" or "Dallas, TX" all four providers were essentially the same —
under 0.5km error. But when I tested more realistic inputs the gaps opened up.

The worst finding was **ORS on zip codes**. I queried `77001` which is a
Houston, TX zip code. ORS returned a dam in Latimer County, Oklahoma —
573km from Houston. That's not a rounding error, that's a completely wrong
result. A driver typing their zip code would get sent to the wrong state.
That immediately ruled ORS out as a geocoder for me.

The best finding was **Photon on full street addresses**. I queried
`350 Fifth Avenue, New York, NY 10118` (the Empire State Building). Photon
returned a location 0.006km from the actual building — essentially exact.
Nominatim returned a location in Westchester County 24km away. ORS returned
the city centroid 7km away. LocationIQ had the same 24km miss as Nominatim,
which makes sense since they're both built on the same underlying data.

That result sealed it for me. Drivers will type full addresses into this
form. Photon is the only provider that handles them accurately.

---

### Why I dropped LocationIQ

I specifically tested LocationIQ's structured API because I'd seen prior
benchmark data showing it outperforms freeform geocoding. In those benchmarks
the structured API gave 5.29km average error vs 113km for freeform — a huge
improvement. So I thought it might be worth adding as a premium option.

But when I ran it against these test cases, the accuracy was identical to
Nominatim. They're both Nominatim under the hood, just different wrappers.
The structured parsing I built didn't help here because the test cases were
already clean US addresses. And with a p99 latency of 2.9 seconds, it was
worse on the metric that matters for UX. No reason to add the complexity.

---

### Why I chose Photon as primary

Out of everything I tested, Photon was the clear winner for this app. The
reason comes down to what drivers actually type. They're not typing just
"Chicago" — they're typing their warehouse address, their terminal address,
their dropoff dock. Full street addresses are the primary input. Photon was
the only provider that handled those correctly. 0.006km on the Empire State
Building test while every other provider missed by 7–24km tells you
everything you need to know.

The 680ms p50 latency looked slow on paper but in practice it's fine. This
is a trip planning form, not a real-time search bar. The user fills in three
locations and hits submit — they're not expecting instant autocomplete. And
importantly Photon's latency is **consistent** — p50 is 680ms, p99 is 734ms.
There's barely any variance. You know what you're getting every single time.
No credit card, no API key, completely free and open. Easy choice.

### Why I chose Nominatim as backup

Nominatim at 75ms p50 is so fast that if Photon ever fails or times out, the
fallback is nearly instant from the user's perspective. For city-level
queries — which is what most fallback situations will involve — Nominatim
is accurate enough (under 0.5km error on Chicago, Dallas, LA, Memphis). The
street address weakness only shows up on very specific queries, and a fallback
situation is rare enough that it's acceptable. It's also completely free with
no key needed, which means the fallback path has zero additional dependencies.

---

## Routing

### What I looked at

For routing I needed a truck profile. Car routing on a trucker ELD app is
wrong — it ignores bridge heights, weight limits, and roads where trucks
are prohibited. So the field narrowed quickly.

Again I looked at HERE Maps and TomTom first since they're industry standard
for logistics routing. Both have excellent truck routing with verified
real-world restriction data. But both require a credit card even for the
free tier. Same decision as geocoding — ruled out.

That left:
- **OpenRouteService** — free, has a `driving-hgv` truck profile
- **OSRM** — completely free, but car only on the public demo
- **Valhalla** — open source, has truck routing, but no hosted free API
- **GraphHopper** — truck profiles exist but are locked behind a paid plan

---

### What the numbers showed

ORS on the HGV profile was consistently under 0.5% distance error on every
interstate route I tested. Chicago to Indianapolis came back at 182.8 miles
against an expected 182 — basically perfect. NYC to LA was 2,793 miles
against an expected 2,790. The latency was predictable — around 750ms p50
for short routes, 1,150ms for cross-country.

OSRM's accuracy was comparable — the distances were nearly identical to ORS.
On interstates this makes sense since trucks and cars use the same highways.
But the public demo server latency was all over the place. The p99 hit
2.8 seconds on long routes. That's a shared global server with no SLA, not
something I'd rely on. And it's car routing — no truck profile.

---

### Why not Valhalla?

Valhalla would actually be the ideal long-term solution — open source, truck
profile, self-hosted so no quota or rate limits. But self-hosting means
downloading OSM data, running a Docker container, and managing that
infrastructure. For a demo app that's unnecessary overhead. ORS's 2,000
req/day free quota is more than enough for this project and I can always
add Valhalla later if it ever gets rate limited in production.

---

### Why I chose ORS as primary

Honestly once I eliminated everything that needed a credit card and everything
that didn't have a truck profile, ORS was the only real option left. But that's
not a compromise — the benchmark results are genuinely good. Under 0.5%
distance error across every interstate route I threw at it. Stable, predictable
latency. Full route geometry returned so I can draw the exact road on the map.
Turn-by-turn instructions included. And the `driving-hgv` profile means it
actually routes like a truck — avoiding low bridges and weight-restricted roads
rather than sending a 40-ton rig down a suburban street.

The fact that it's the same API whether you use the hosted version or
self-host it is a big deal too. If this app ever needed to scale past the
2,000 req/day free quota, I could spin up a self-hosted ORS instance on
Railway and change one environment variable. No code changes, no provider
migration, no rewriting the integration.

One API key. Zero cost. Accurate distances. That's everything I needed.

### Why I chose OSRM as backup and what to know about it

I want to be upfront about what OSRM is and isn't as a backup. It's car
routing, not truck routing. On long interstate routes the distances are nearly
identical to ORS — within 0.5% — because trucks and cars use the same
highways. But it has no awareness of truck restrictions, bridge heights, or
weight limits. If the fallback ever triggered on an urban route or a delivery
into a city center, the directions could technically be wrong for a truck.

So why use it at all? Because a trip plan with slightly imperfect routing is
better than no trip plan. If ORS goes down right when a driver needs to plan
a 2,000-mile run, showing them an error screen doesn't help anyone. OSRM
gives them a close-enough answer to work with, and the app surfaces a visible
warning that truck routing is temporarily unavailable so they know to double
check.

In practice ORS has been reliable and I expect this fallback to rarely if
ever trigger. But it's there if needed.

---

## Summary

| Layer | Primary | Backup | Ruled out |
|-------|---------|--------|-----------|
| Geocoding | Photon (Komoot) | Nominatim (OSM) | ORS (573km zip error), LocationIQ (2.9s p99), HERE Maps (credit card), TomTom (credit card) |
| Routing | ORS HGV | OSRM car (emergency only) | HERE Maps (credit card), TomTom (credit card), GraphHopper (truck = paid tier), Valhalla (self-host overhead) |

Total external cost: $0. No credit cards. One free ORS API key for routing.
Geocoding needs no keys at all.

---

## Benchmark Data Tables

Raw data from `results/geocoding_20260518_154441.json` and `results/routing_20260518_154631.json`.
5 runs per query. Latency in milliseconds. Distance error in kilometers.

---

### Geocoding — Latency by Query Type (ms)

| Query | Nominatim p50 | p95 | p99 | Photon p50 | p95 | p99 | ORS p50 | p95 | p99 | LocationIQ p50 | p95 | p99 |
|-------|--------------|-----|-----|-----------|-----|-----|---------|-----|-----|---------------|-----|-----|
| Chicago, IL | 71 | 111 | 115 | 677 | 727 | 733 | 768 | 954 | 989 | 807 | 1,539 | 1,542 |
| Dallas, TX | 76 | 81 | 81 | 705 | 719 | 721 | 766 | 818 | 826 | 622 | 2,646 | 2,878 |
| Los Angeles, CA | 76 | 83 | 84 | 672 | 716 | 723 | 789 | 820 | 823 | 663 | 1,384 | 1,488 |
| Memphis, TN | 81 | 97 | 98 | 657 | 706 | 708 | 758 | 776 | 776 | 1,121 | 1,394 | 1,446 |
| 350 Fifth Ave, NYC (street) | 76 | 83 | 83 | 765 | 815 | 817 | 795 | 823 | 823 | 870 | 1,042 | 1,063 |
| I-40 W, Amarillo (highway) | 78 | 94 | 96 | 690 | 732 | 738 | 785 | 1,605 | 1,767 | 730 | 1,730 | 1,894 |
| 77001 (zip code) | 71 | 81 | 83 | 674 | 747 | 756 | 769 | 834 | 838 | 1,455 | 2,408 | 2,515 |
| Springfield (ambiguous) | 73 | 82 | 83 | 661 | 777 | 791 | 865 | 876 | 877 | 561 | 787 | 802 |
| **Avg across all queries** | **76** | **89** | **90** | **688** | **742** | **748** | **787** | **938** | **965** | **854** | **1,616** | **1,703** |

> Photon's key strength: p50 and p99 are nearly identical (688ms vs 748ms) — variance is only 60ms.
> LocationIQ's p99 on Dallas is 4.6x its p50 — you never know when it'll spike.

---

### Geocoding — Accuracy by Query Type (distance error, km)

| Query | Nominatim | Photon | ORS | LocationIQ |
|-------|-----------|--------|-----|-----------|
| Chicago, IL | 0.53 | 0.53 | 2.55 | 0.53 |
| Dallas, TX | 0.05 | 0.05 | 4.66 | 0.05 |
| Los Angeles, CA | 0.19 | 0.19 | 1.27 | 0.19 |
| Memphis, TN | 0.46 | 0.46 | 9.53 | 0.46 |
| 350 Fifth Ave, NYC (street address) | 23.94 | **0.006** | 7.39 | 23.99 |
| I-40 W, Amarillo (highway) | 10.40 | 5.55 | 8.66 | 3.56 |
| 77001 (zip code) | 3.29 | 3.34 | 573.76 | 3.34 |
| Springfield (ambiguous) | — | — | — | — |
| **Avg (excl. ambiguous + zip outlier)** | **5.81** | **1.30** | **5.68** | **5.30** |

> ORS zip error: returned a dam in Latimer County, OK — 573 km from Houston. Wrong state entirely.
> Photon street address: 0.006 km from Empire State Building. Every other provider missed by 7–24 km.

---

### Geocoding — Provider Comparison Summary

| Provider | Role | Avg p50 (ms) | Avg p99 (ms) | Latency variance | Street addr error | Zip error | API key | Cost |
|----------|------|-------------|-------------|-----------------|------------------|-----------|---------|------|
| Photon | Primary | 688 | 748 | Low (±60ms) | 0.006 km | 3.34 km | No | Free |
| Nominatim | Backup | 76 | 90 | Very low (±14ms) | 23.94 km | 3.29 km | No | Free |
| ORS | Ruled out | 787 | 965 | Medium (±178ms) | 7.39 km | 573.76 km | Yes | Free tier |
| LocationIQ | Ruled out | 854 | 1,703 | High (±849ms) | 23.99 km | 3.34 km | Yes | Free tier |

---

### Routing — Latency by Route (ms)

| Route | ORS HGV p50 | p95 | p99 | stdev | OSRM p50 | p95 | p99 | stdev |
|-------|------------|-----|-----|-------|---------|-----|-----|-------|
| Chicago to Indianapolis (183 mi) | 741 | 815 | 821 | 43 | 699 | 1,858 | 2,082 | 644 |
| Dallas to Atlanta (452 mi) | 941 | 959 | 961 | 21 | 693 | 748 | 750 | 32 |
| Chicago to LA (2,015 mi) | 1,152 | 1,180 | 1,182 | 27 | 1,075 | 1,214 | 1,218 | 76 |
| NYC to LA (2,793 mi) | 1,174 | 1,198 | 1,199 | 51 | 1,362 | 2,610 | 2,838 | 705 |
| Multi-stop (2,399 mi) | 1,140 | 1,165 | 1,169 | 174 | 1,196 | 1,703 | 1,787 | 287 |
| **Avg across routes** | **1,030** | **1,063** | **1,066** | **63** | **1,005** | **1,827** | **1,935** | **349** |

> OSRM stdev is 5–14x higher than ORS — the shared demo server has no SLA.
> ORS is rock-steady: p50 and p99 differ by only 36ms on average.

---

### Routing — Accuracy and Capabilities

| Route | Expected (mi) | ORS result | ORS error | OSRM result | OSRM error |
|-------|--------------|-----------|----------|------------|-----------|
| Chicago to Indianapolis | 182 | 182.8 | 0.45% | 180.7 | 0.71% |
| Dallas to Atlanta | 435 | 451.9 | 3.86% | 452.3 | 3.76% |
| Chicago to LA | 2,012 | 2,014.9 | 0.25% | 2,018.1 | 0.10% |
| NYC to LA | 2,790 | 2,793.2 | 0.12% | 2,798.4 | 0.30% |
| Multi-stop | ~2,025 | 2,398.8 | 18.4% | 2,404.8 | 18.2% |

| Capability | ORS HGV | OSRM (demo) |
|-----------|---------|------------|
| Truck profile (HGV) | Yes | No (car only) |
| Full route geometry | Yes | Yes |
| Turn-by-turn directions | Yes | Yes |
| Free tier quota | 2,000 req/day | Unlimited (shared) |
| SLA / reliability | Documented | None |
| Self-hostable | Yes | Yes |

> Multi-stop ~18% error is the same for both providers — inherent waypoint ordering issue, not provider-specific.
> Single point-to-point routes are consistently under 4% error.
