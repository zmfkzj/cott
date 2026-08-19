# expense-split

## Purpose
Calculate exact cent balances for one expense and settle them with a transfer list.

## Key points
- Validate the payer, participants, amount, duplicate participants, and payer inclusion in that fixed precedence; then distribute evenly among alphabetically ordered participants and assign remaining cents from the beginning.
- Sort debtors and creditors alphabetically, greedily transfer the smaller remaining balance at a time, and have the top-level function propagate balance-calculation errors unchanged.
