"""
Bill-split settlement calculator.

Usage:
    python settle.py expenses.json
    python settle.py --example

Input JSON schema:
    {
      "participants": ["Alice", "Bob", "Carol"],
      "expenses": [
        {
          "description": "Dinner",
          "paid_by": "Alice",
          "amount": 120.00,
          "currency": "USD",          # optional, defaults to settlement_currency
          "split_among": ["Alice", "Bob", "Carol"],   # omit → all participants
          "split_type": "equal"        # "equal" | "percentage" | "fixed"
          # for percentage: "splits": {"Alice": 0.5, "Bob": 0.3, "Carol": 0.2}
          # for fixed:      "splits": {"Alice": 60, "Bob": 36, "Carol": 24}
        }
      ],
      "settlement_currency": "USD"
    }
"""

import json
import sys
from collections import defaultdict


def parse_expenses(data: dict) -> tuple[list[str], dict[str, float]]:
    participants = data.get("participants", [])
    settlement_currency = data.get("settlement_currency", "USD")
    net: dict[str, float] = defaultdict(float)

    for p in participants:
        net[p] += 0  # ensure every participant appears

    for i, exp in enumerate(data.get("expenses", []), 1):
        desc = exp.get("description", f"Expense {i}")
        paid_by = exp["paid_by"]
        amount = float(exp["amount"])
        covered = exp.get("split_among") or participants
        split_type = exp.get("split_type", "equal")

        if not covered:
            raise ValueError(f"Expense '{desc}': split_among is empty")

        if split_type == "equal":
            share = amount / len(covered)
            for p in covered:
                net[p] -= share
        elif split_type == "percentage":
            splits = exp.get("splits", {})
            total_pct = sum(splits.values())
            if abs(total_pct - 1.0) > 0.001:
                raise ValueError(
                    f"Expense '{desc}': percentages sum to {total_pct:.3f}, expected 1.0"
                )
            for p, pct in splits.items():
                net[p] -= amount * pct
        elif split_type == "fixed":
            splits = exp.get("splits", {})
            total_fixed = sum(splits.values())
            if abs(total_fixed - amount) > 0.01:
                raise ValueError(
                    f"Expense '{desc}': fixed splits sum to {total_fixed:.2f}, expected {amount:.2f}"
                )
            for p, fixed in splits.items():
                net[p] -= fixed
        else:
            raise ValueError(f"Expense '{desc}': unknown split_type '{split_type}'")

        net[paid_by] += amount

    return settlement_currency, dict(net)


def minimize_transactions(net: dict[str, float]) -> list[tuple[str, str, float]]:
    creditors = sorted(
        ((p, v) for p, v in net.items() if v > 0.005), key=lambda x: -x[1]
    )
    debtors = sorted(
        ((p, -v) for p, v in net.items() if v < -0.005), key=lambda x: -x[1]
    )
    creditors = list(creditors)
    debtors = list(debtors)

    transactions = []
    ci, di = 0, 0
    while ci < len(creditors) and di < len(debtors):
        cp, c_bal = creditors[ci]
        dp, d_bal = debtors[di]
        transfer = min(c_bal, d_bal)
        transactions.append((dp, cp, round(transfer, 2)))
        c_bal -= transfer
        d_bal -= transfer
        creditors[ci] = (cp, c_bal)
        debtors[di] = (dp, d_bal)
        if c_bal < 0.005:
            ci += 1
        if d_bal < 0.005:
            di += 1

    return transactions


AMBIGUOUS_SYMBOL_CURRENCIES = {"JPY", "CNY"}

CURRENCY_SYMBOL = {"USD": "$", "EUR": "€", "GBP": "£", "CNY": "¥", "JPY": "¥"}


def format_amount(amount: float, currency: str) -> str:
    """Format amount with symbol; append currency code for ¥ to avoid JPY/CNY ambiguity."""
    symbol = CURRENCY_SYMBOL.get(currency, currency + " ")
    formatted = f"{symbol}{amount:.2f}"
    if currency in AMBIGUOUS_SYMBOL_CURRENCIES:
        formatted += f" {currency}"
    return formatted


def print_report(data: dict) -> None:
    currency, net = parse_expenses(data)

    if currency in AMBIGUOUS_SYMBOL_CURRENCIES:
        print(f"Note: amounts shown as ¥ {currency} to distinguish from the other ¥ currency.")

    total_net = sum(net.values())
    if abs(total_net) > 0.01:
        print(f"WARNING: net balances sum to {total_net:.4f} (expected 0). Check your data.")

    print("\n=== Net Balances ===")
    print(f"{'Person':<12} {'Net':>16}")
    print("-" * 30)
    for p, bal in sorted(net.items()):
        arrow = "owes" if bal < -0.005 else ("is owed" if bal > 0.005 else "settled")
        print(f"{p:<12} {format_amount(bal, currency):>16}  ({arrow})")

    txns = minimize_transactions(net)
    print(f"\n=== Settlement Instructions ({len(txns)} transaction(s)) ===")
    if not txns:
        print("Everyone is already settled up!")
    for idx, (debtor, creditor, amount) in enumerate(txns, 1):
        print(f"  {idx}. {debtor} → {creditor}   {format_amount(amount, currency)}")
    print()


EXAMPLE = {
    "participants": ["Alice", "Bob", "Carol"],
    "expenses": [
        {
            "description": "Groceries",
            "paid_by": "Alice",
            "amount": 90.00,
            "split_among": ["Alice", "Bob", "Carol"],
            "split_type": "equal",
        },
        {
            "description": "Gas",
            "paid_by": "Bob",
            "amount": 60.00,
            "split_among": ["Bob", "Carol"],
            "split_type": "equal",
        },
        {
            "description": "Dessert",
            "paid_by": "Carol",
            "amount": 30.00,
            "split_among": ["Alice", "Bob", "Carol"],
            "split_type": "equal",
        },
    ],
    "settlement_currency": "USD",
}


if __name__ == "__main__":
    if len(sys.argv) == 1 or (len(sys.argv) == 2 and sys.argv[1] == "--example"):
        print("Running built-in example...")
        print_report(EXAMPLE)
    else:
        with open(sys.argv[1], encoding="utf-8") as f:
            data = json.load(f)
        print_report(data)
