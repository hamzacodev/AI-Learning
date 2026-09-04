# RouteAI

RouteAI is Nexara's flagship route-optimization product, first released in production as v1.0 on 22 January 2019. It plans multi-stop delivery and line-haul routes for fleets ranging from 50 to 5,000 vehicles.

## What it does

RouteAI ingests order manifests, vehicle capacity constraints, driver hours-of-service rules, live traffic feeds, and port-congestion data, then solves for the lowest-cost feasible route set. The solver combines a hybrid heuristic — adaptive large neighbourhood search — with a gradient-boosted travel-time model trained on 2.8 billion historical trip segments.

Typical customers see a 14–19% reduction in cost per delivered kilometre within the first two quarters. Kestrel Freight BV, the original 2018 pilot customer, reported an 17.3% fuel-cost reduction across 120 vehicles in its first full year.

## Key capabilities

- **Dynamic re-planning**: routes recalculated every 90 seconds against live conditions.
- **Constraint library**: 47 built-in constraint types including cold-chain temperature windows, ADR hazardous-goods restrictions, and EU driver rest rules under Regulation (EC) 561/2006.
- **Scenario simulation**: planners can model fleet-size or depot-location changes before committing capital.
- **API-first**: REST and gRPC endpoints, with a median solve latency of 340 ms for a 200-stop problem.

## Technical details

The solver runs on Kubernetes across three regions (eu-west-1, us-east-2, ap-southeast-1). RouteAI is licensed per active vehicle per month, starting at €38 per vehicle, with volume tiers beginning at 500 vehicles. The RouteAI team is led by Marcus Oyelaran and currently numbers 34 engineers.
