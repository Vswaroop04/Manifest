# Frontend — React App

React 18 + TypeScript + Vite frontend. Handles the trip input form, Leaflet map with route and stop markers, SVG log sheet grid, and trip history.

---

## Stack

- **Framework**: React 18, TypeScript, Vite
- **Styling**: Tailwind CSS v4 + shadcn/ui primitives
- **Map**: React-Leaflet + OpenStreetMap tiles
- **Forms**: React Hook Form + Zod
- **Data fetching**: TanStack Query
- **State**: Zustand (tab state)
- **i18n**: lightweight custom hook (`useTranslation`)

---

## Setup

```bash
npm install
cp .env.example .env.local
```

`.env.local`:

```bash
VITE_API_BASE_URL=http://localhost:8000
```

```bash
npm run dev        # dev server on :5173
```

---

## Scripts

| Command | What it does |
|---------|-------------|
| `npm run dev` | Vite dev server on port 5173 |
| `npm run build` | Production build to `dist/` |
| `npm run preview` | Preview the production build locally |
| `npm run typecheck` | `tsc --noEmit` — type check without emitting |
| `npm run lint` | ESLint across all source files |

---

## Project layout

```
src/
├── components/
│   ├── TripForm/
│   │   ├── TripForm.tsx        # React Hook Form + Zod schema, all fields
│   │   ├── AddressInput.tsx    # Debounced autocomplete against /api/geocode/
│   │   └── NumberStepper.tsx   # Cycle hours input with +/- buttons
│   ├── RouteMap/
│   │   └── RouteMap.tsx        # React-Leaflet map, polyline, stop markers
│   ├── LogSheet/
│   │   ├── LogSheet.tsx        # Renders one LogSheetDay per day
│   │   └── LogSheetDay.tsx     # Hand-drawn SVG 24-hour FMCSA grid
│   ├── TripSummary/
│   │   └── TripSummary.tsx     # Miles, drive time, days, cycle usage
│   ├── TripHistory/
│   │   └── TripHistory.tsx     # Past trips list via TanStack Query
│   └── ui/                     # shadcn/ui primitives (Button, Card, Input…)
├── hooks/
│   └── useTranslation.ts       # Reads from locales/en.json
├── services/
│   └── api.ts                  # All fetch calls — planTrip, getTripList, getTripDetail
├── store/
│   └── tripStore.ts            # Zustand — active tab, selected event
├── types/
│   └── trip.ts                 # TypeScript types matching backend response
└── utils/
    └── geo.ts                  # ORS [lng,lat] → Leaflet [lat,lng] flip
```

---

## Key design decisions

### Why React-Leaflet

OpenStreetMap tiles are free with no API key. React-Leaflet wraps Leaflet.js as declarative React components (`<Marker>`, `<Polyline>`, `<Popup>`). Google Maps and Mapbox both require a billing-enabled API key.

### Why TanStack Query

`useMutation` for the trip plan call gives `isPending`, `isError`, and `error` for free — no manual loading state. `useQuery` for trip history caches the list and `invalidateQueries` auto-refreshes it when a new trip is saved.

### Why the log sheet is plain SVG

The 24-hour grid math is trivial: `x = LABEL_W + start_min`, `width = end_min - start_min` (1px = 1 minute). SVG scales to any resolution and prints crisply. `html2canvas` would produce a blurry rasterized image. A charting library would add hundreds of KB for a grid that's 20 lines of SVG.

### Lazy-loaded map

Leaflet is ~200 KB. The `RouteMap` component is `lazy()`-imported so it only downloads after a trip result exists. `<Suspense>` shows a placeholder while it loads.

### Coordinate convention

ORS returns `[longitude, latitude]`. Leaflet expects `[latitude, longitude]`. The flip happens once in `utils/geo.ts` (`orsToLeaflet`), never inline in a component.

---

## Deploying to Vercel / Netlify

Both detect Vite automatically.

**Vercel:**
```bash
vercel --prod
```
Set `VITE_API_BASE_URL` to your Railway backend URL in the Vercel project settings.

**Netlify:**
```bash
netlify deploy --prod --dir=dist
```
Add `VITE_API_BASE_URL` as an environment variable in the Netlify dashboard.

The app is a pure static SPA — no server-side rendering needed.
