# Bill Split Settlement Skill

A Claude Code skill that takes a list of shared expenses, computes each person's net balance, and produces the **minimum number of payment instructions** needed to settle all debts.

---

## What the Skill Does

Given a group of people and a list of expenses (who paid, how much, who it covered), the skill:

1. Parses expenses from natural language, tables, or bullet lists
2. Computes each person's net balance (`total paid − total owed`)
3. Applies a greedy algorithm to produce the fewest possible transfer instructions
4. Outputs three sections: an expense summary table, net balances, and settlement instructions

It handles equal splits, percentage splits, fixed-amount splits, partial participants (not everyone joins every expense), and multi-currency inputs with user-provided exchange rates.

---

## Why I Chose It

Splitting bills after a group trip or shared event is a universal, recurring pain point. The math is straightforward in theory but error-prone in practice — especially when:

- Different people paid for different subsets of the group
- Someone covered a larger share by agreement
- The group wants to minimize how many Venmo/transfers they send

This use case maps cleanly onto a structured skill: the inputs and outputs are well-defined, the logic is deterministic, and Claude adds value by accepting messy natural-language input and producing a clean, trustworthy result. It is also a good testbed for edge-case handling (ambiguous currency symbols, bad percentage inputs, payment-link requests that are out of scope).

---

## How to Use It

### As a Claude Code custom command

Copy the skill definition into `.claude/commands/`:

```bash
cp .claude/skills/bill-split-settlement/SKILL.md .claude/commands/bill-split-settlement.md
```

Then trigger it in any Claude Code conversation:

```
/project:bill-split-settlement
```

Paste your expense data in any format — prose, a table, or a bullet list — and Claude will walk through the calculation.

**Example prompt:**

> Alice paid $120 for the hotel for all four of us. Bob paid $80 for groceries, split equally among everyone. Carol paid $40 for breakfast, just for her and Alice. Settle this up.

### As a standalone Python script

```bash
# Built-in example
python .claude/skills/bill-split-settlement/scripts/settle.py --example

# Custom data file
python .claude/skills/bill-split-settlement/scripts/settle.py path/to/expenses.json
```

**Input JSON format:**

```json
{
  "participants": ["Alice", "Bob", "Carol"],
  "settlement_currency": "USD",
  "expenses": [
    {
      "description": "Dinner",
      "paid_by": "Alice",
      "amount": 120.00,
      "split_among": ["Alice", "Bob", "Carol"],
      "split_type": "equal"
    },
    {
      "description": "Hotel (weighted)",
      "paid_by": "Bob",
      "amount": 200.00,
      "split_type": "percentage",
      "splits": { "Alice": 0.5, "Bob": 0.3, "Carol": 0.2 }
    }
  ]
}
```

See [`assets/example-expenses.json`](.claude/skills/bill-split-settlement/assets/example-expenses.json) for a complete example.

---

## What the Script Does

[`scripts/settle.py`](.claude/skills/bill-split-settlement/scripts/settle.py) is a self-contained Python 3.10+ calculator with three functions:

| Function | Responsibility |
|---|---|
| `parse_expenses(data)` | Reads the JSON input, validates splits (percentages must sum to 1.0, fixed amounts must sum to total), and returns a `net` dict mapping each person to their running balance |
| `minimize_transactions(net)` | Greedy algorithm: repeatedly pairs the largest creditor with the largest debtor until all balances reach zero. Produces at most `n − 1` transactions for `n` participants |
| `format_amount(amount, currency)` | Formats currency amounts; appends the currency code (e.g., `¥1,500 JPY`) when the symbol is ambiguous (¥ is shared by JPY and CNY) |

The script raises a `ValueError` with a descriptive message on bad input (mismatched percentages, empty split lists, unknown split types) rather than silently producing wrong output.

---

## What Worked Well

- **Natural-language input tolerance** — Claude's parsing step handles messy, real-world descriptions without requiring a rigid format from the user.
- **Greedy algorithm correctness** — For typical group sizes (< 20 people), the greedy approach reliably produces near-optimal or optimal transaction counts.
- **Input validation with clear errors** — Catching bad percentage sums and mismatched fixed splits before computing prevents silent wrong answers.
- **¥ ambiguity handling** — Explicitly flagging JPY vs. CNY confusion (a ~20× difference) prevents a class of silent, expensive errors.
- **Scope refusal** — The skill produces settlement amounts but explicitly declines to generate payment links, keeping the output trustworthy and the scope contained.
- **Multi-split-type support** — Equal, percentage, and fixed splits cover the vast majority of real-world scenarios in a single skill.

---

## Limitations That Remain

| Limitation | Detail |
|---|---|
| **No exchange-rate lookup** | Multi-currency inputs require the user to supply exchange rates manually. The skill cannot fetch live rates. |
| **Greedy is not always globally optimal** | The minimum-transaction problem is NP-hard in general. The greedy algorithm is optimal for most practical cases but can produce one extra transaction in rare configurations with many participants. |
| **No persistent state** | Each conversation is stateless. The skill cannot track a running tab across multiple sessions (use Splitwise or similar for that). |
| **¥ still requires user confirmation** | The script correctly labels output, but if the user does not clarify upfront, the conversation stalls waiting for their answer before any calculation runs. |
| **Rounding accumulation** | With many expenses and many participants, repeated floating-point rounding can cause the net-balance sanity check to trip on legitimate data. A future fix would use `decimal.Decimal` throughout. |
| **No partial-payment support** | If someone has already paid back part of their debt outside this system, the skill has no way to account for it without the user manually adjusting the input amounts. |