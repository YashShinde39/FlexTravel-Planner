# ADR-0008: Stop/landmark search, map pins, Nominatim; landmarks from OSM

- Status: Accepted
- Date: 2026-10-23

## Context

Visitors (ADR-0001) think in landmarks and addresses ("Red Fort", "AIIMS"), not stop
names. Options range from free OpenStreetMap services to the paid Google Places API.

## Decision

- **Location input:** search stops and landmarks, drop a pin on a map
  (Leaflet + OpenStreetMap tiles), or search addresses through **Nominatim**
  (OpenStreetMap's free geocoder).
- **Landmark data:** imported from **OpenStreetMap** (monuments, hospitals, colleges,
  markets, malls and so on) into PostGIS, as a pipeline stage.
- Arbitrary points connect to the network through access legs (ADR-0004).

## Alternatives considered

- **Stops + pin only.** Reliable but inconvenient for visitors.
- **Google Places.** The best Indian address search, but it needs billing and an API key.
- **Curated landmark list.** High quality but tiny.
- **Geocoder only, for landmarks too.** Slower and less reliable for Indian names.

## Consequences

- Nominatim's public instance has a strict usage policy (about 1 request per second,
  identifying user agent, no bulk use). Requests must be debounced and cached, or a
  self-hosted instance used.
- OSM data is licensed under the ODbL, so attribution is required in the UI.
- OSM coverage of Indian addresses is patchy; landmark search compensates.

## Why (in my words)

> _To fill in: why landmarks first for visitors? Why free OSM data over Google?_

## Questions an interviewer might ask

- How do you rank search results when "Rajiv Chowk" is both a metro station and a market?
- What are Nominatim's limits, and how does your design respect them?
