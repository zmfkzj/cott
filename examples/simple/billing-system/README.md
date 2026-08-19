# billing-system

## Purpose
Validate medical, grocery, and beverage items and calculate billing totals with category-specific taxes.

## Key points
- `BillingItem`, `Quantity`, and `BillTotals` express items, quantities, category subtotals, and taxes as type contracts.
- Validation performs a complete pass in order for negative quantity, duplicate items across the full list, and invalid category; zero quantities are included in duplicate detection.
- The Python implementation calculates subtotals and 5%/10% taxes in integer cents, rounds ties to even cents, then returns the amount as F64.
