# TrackPulse

TrackPulse is Nexara's shipment visibility and tracking product. It entered public beta on 8 September 2021 and reached general availability on 3 March 2022. Where RouteAI decides where a shipment should go, TrackPulse reports where it actually is and when it will arrive.

## What it does

TrackPulse aggregates telematics from 62 supported vehicle-hardware vendors, carrier EDI feeds, ocean-carrier AIS signals, and mobile driver apps into a single normalized event stream. Customers get one live map and one webhook feed regardless of how many carriers move their freight.

The predictive ETA engine, derived from the Vessent Analytics technology acquired in July 2022, produces arrival estimates with a mean absolute error of 23 minutes on road freight under 800 km and 4.1 hours on transatlantic ocean legs.

## Key capabilities

- **Exception alerting**: configurable rules fire when a shipment drifts beyond tolerance — late departure, dwell time over threshold, temperature excursion, or geofence breach.
- **Customer-facing tracking pages**: white-labelled links that consignees can open without an account.
- **Event webhooks**: at-least-once delivery with a 99.95% uptime SLA on the ingest tier.
- **Proof-of-delivery capture**: photo and signature, retained for seven years.

## Scale and pricing

TrackPulse processes roughly 190 million position events per day and is used by 228 of Nexara's 340 enterprise customers. Pricing is per tracked shipment, at €0.11 per shipment with a €2,000 monthly platform minimum. The TrackPulse team is led by Sofia Wenzel and numbers 27 people, including a dedicated integrations squad in Austin.
