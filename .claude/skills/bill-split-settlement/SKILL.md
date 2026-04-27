---
name: bill-split-settlement
description: Calculates how to fairly split shared expenses among a group of people and produces a minimal set of transfer instructions to settle all debts. Use when the user provides a list of expenses (who paid, how much, for whom), asks who owes whom, or wants to figure out how to settle up after a trip, dinner, event, or any group spending scenario. Handles unequal splits, partial participants, and multi-currency input with a designated settlement currency.
---

# Bill Split Settlement Skill

## When to Use This Skill

- User provides a list of group expenses and wants to know how to settle up
- User asks "who owes whom how much" after a trip, meal, event, or any shared spending
- User wants to **minimize the number of transactions** needed to clear all balances
- User wants a structured summary: net balances + settlement instructions
- Expenses involve unequal splits (e.g., Alice didn't join dinner, Bob's share is doubled)

## When NOT to Use This Skill

- The user only wants a simple 50/50 split of a single bill → just divide inline, no skill needed
- No actual expense data is provided (user is just asking how splitting works conceptually)
- The request involves recurring financial tracking or a live ledger → suggest a dedicated app (Splitwise, etc.)
- Legal or tax implications are involved → out of scope
- The user asks for Venmo / PayPal / WeChat Pay / Zelle / any payment links or QR codes → **explicitly decline** (see Payment Links below)

---

## Expected Inputs

The user should provide (in any format — prose, table, bullet list):

| Field | Required | Notes |
|---|---|---|
| **Participants** | Yes | Names or identifiers of everyone in the group |
| **Expenses** | Yes | Each expense: payer, amount, and who it covers |
| **Split rule per expense** | Preferred | "equally among all", "only Alice and Bob", "Bob pays 60%", etc. If omitted, assume equal split among all named participants |
| **Currency** | Optional | Single currency assumed if not specified; if mixed, ask user for a settlement currency and exchange rates |

### Acceptable Input Formats
- Natural language: *"Alice paid $120 for dinner for everyone (4 people). Bob paid $60 for drinks, only for him and Carol."*
- Table or spreadsheet data pasted into chat
- Bullet list of transactions

---

## Step-by-Step Instructions

### Step 1 — Parse and Clarify

1. Extract all expenses into a structured internal list:
   ```
   [payer, amount, covered_participants, split_type]
   ```
2. Identify all unique participants (union of all payers + all covered persons).
3. If any ambiguity exists (missing participants, unclear split), **ask one clarifying question** before proceeding. Do not guess silently on amounts.

### Step 2 — Compute Each Person's Share Per Expense

For each expense:
- **Equal split**: `share = amount / len(covered_participants)`
- **Percentage split**: `share_i = amount × pct_i`
- **Fixed amount split**: use stated amounts; verify they sum to total (warn if not)
- Record: who *paid* vs. who *owes* for this expense

### Step 3 — Compute Net Balances

For each person:
```
net_balance = total_paid_by_person − total_owed_by_person
```
- Positive net → others owe this person money (they are a **creditor**)
- Negative net → this person owes others money (they are a **debtor**)
- Zero net → already settled

**Sanity check**: sum of all net balances must equal 0. If not, flag a data error to the user.

### Step 4 — Minimize Transactions (Greedy Settlement)

Use the greedy minimum-transaction algorithm:

```
1. Separate participants into creditors (net > 0) and debtors (net < 0)
2. Sort both lists by absolute value, descending
3. Repeat until all balances are zero:
   a. Take the largest creditor C and largest debtor D
   b. transfer = min(|balance_C|, |balance_D|)
   c. Record: "D pays C: transfer_amount"
   d. Reduce both balances by transfer
   e. Remove any participant whose balance reaches 0
```

This produces at most `n − 1` transactions for `n` participants.

### Step 5 — Format and Present Output

Produce the output in three sections (see Output Format below).

---

## Expected Output Format

### Section 1: Expense Summary Table

| # | Description | Paid By | Amount | Split Among | Each Pays |
|---|---|---|---|---|---|
| 1 | Dinner | Alice | $120.00 | Alice, Bob, Carol, Dave | $30.00 |
| 2 | Drinks | Bob | $60.00 | Bob, Carol | $30.00 |

### Section 2: Net Balances

| Person | Total Paid | Total Owed | Net Balance |
|---|---|---|---|
| Alice | $120.00 | $30.00 | **+$90.00** ✅ |
| Bob | $60.00 | $60.00 | $0.00 ✅ |
| Carol | $0.00 | $60.00 | **−$60.00** |
| Dave | $0.00 | $30.00 | **−$30.00** |

> ✅ Net sum = $0.00 (balanced)

### Section 3: Settlement Instructions

Minimum transactions needed: **2**

```
1. Carol  →  Alice   $60.00
2. Dave   →  Alice   $30.00
```

Present as a clear, copy-pasteable list. If the user's currency is non-USD, use that symbol. Round to 2 decimal places.

---

## Multi-Currency Handling

If expenses are in different currencies:
1. Ask the user: *"Expenses are in multiple currencies. What currency should I use for settlement, and what exchange rates should I apply?"*
2. Convert all amounts to the settlement currency before computing balances.
3. Note the exchange rates used in the output.

Do **not** silently assume exchange rates.

### ¥ Symbol Ambiguity

The ¥ symbol is shared by **Japanese Yen (JPY)** and **Chinese Yuan (CNY/RMB)**. They differ by roughly 20×, so the distinction is critical. Whenever ¥ appears in user input, stop and ask before computing:

> "Does ¥ refer to Japanese Yen (JPY) or Chinese Yuan (CNY)? The two currencies differ by ~20× and I cannot assume which one you mean."

Always display amounts with the currency code to avoid confusion (e.g., `¥1,500 JPY` or `¥1,500 CNY`), never bare ¥ alone in output.

---

## Payment Links — Explicit Refusal

If the user asks to generate Venmo / PayPal / WeChat Pay / Zelle / Cash App links, QR codes, or any payment requests, respond with **exactly this refusal pattern** before or after providing the settlement amounts:

> "I can calculate who owes whom and how much, but generating payment links or initiating transfers is outside the scope of this skill. Please use the amounts below to send payments manually through your preferred app."

Rules:
- **Always** provide the settlement amounts even when declining the link request — do not withhold the calculation.
- **Never** attempt to construct a Venmo URL (e.g., `venmo.com/u/...`), PayPal.me link, or any equivalent.
- If the entire request is only about generating links (no expense data provided), decline and explain the scope in one sentence.

---

## Important Limitations and Checks

| Check | Action |
|---|---|
| Net balances don't sum to zero | Flag as data error; list which expense may have incorrect amounts |
| A participant appears as covered but never named upfront | Add them to the participant list; note the addition |
| Expense amounts are ambiguous (e.g., "about $50") | Ask for exact amounts before computing |
| User provides a percentage split that doesn't sum to 100% | Warn and ask for correction before proceeding |
| More than ~10 participants or ~20 expenses | Still apply the same algorithm; consider offering an artifact/table output for readability |
| User asks for Venmo/PayPal/WeChat Pay/Zelle links or QR codes | Decline with the refusal script above; still provide settlement amounts |
| Input contains bare ¥ symbol | Ask whether it means JPY or CNY before computing; display output as `¥X.XX JPY` or `¥X.XX CNY` |

---

## Example

**Input:**
> Alice paid $90 for groceries for Alice, Bob, Carol. Bob paid $60 for gas for Bob and Carol. Carol paid $30 for dessert for everyone.

**Expected flow:**
1. Parse → 3 expenses, 3 participants
2. Compute shares
3. Net: Alice +$50, Bob −$10, Carol −$40
4. Settle: Carol → Alice $40, Bob → Alice $10
5. Output: summary table + net table + 2 settlement instructions
