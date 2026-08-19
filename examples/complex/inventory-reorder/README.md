# inventory-reorder

## Purpose
Determine reorder quantities per SKU while accounting for reserved inventory.

## Key points
- Reject an empty SKU first; if reserved quantity exceeds on-hand quantity, return `ReservedExceedsOnHand` without performing an unsafe subtraction. Then check whether the target level is below the reorder point.
- If available inventory is at or below the reorder point, order enough to fill the target level; otherwise, return a plan with quantity 0.
