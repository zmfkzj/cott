# website-connectivity

## Purpose
Validate caller-provided HTTP observations and classify a website's connectivity status.

## Key points
- The `WebsiteObservation` and `WebsiteClassification` structs fix the URL and status code as the input/output contract.
- An empty URL produces `EmptyUrl` before the status code is considered, and codes outside 100–599 return `InvalidStatusCode`.
- The Python implementation classifies only 200 as `Working` and all other valid HTTP statuses as `NotWorking`; list processing preserves the first error and input order.
