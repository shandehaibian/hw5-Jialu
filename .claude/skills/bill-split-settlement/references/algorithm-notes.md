# Settlement Algorithm Reference

## Greedy Minimum-Transaction Algorithm

Given `n` participants with net balances summing to zero, the greedy algorithm
produces at most `n − 1` transactions.

### Proof of bound
Each transaction zeros out at least one participant's balance. With `n`
participants there are at most `n − 1` transactions before all are settled.

### Optimality note
The greedy approach is **not always globally optimal** (NP-hard in general), but
it is optimal in the common case where each creditor/debtor pair is matched one
at a time in descending order of absolute balance. For typical group sizes
(< 20) it produces near-optimal or optimal results.

### Complexity
- Sorting: O(n log n)
- Main loop: O(n)
- Overall: O(n log n)

## References

- Verhoeven, B. (2014). *Optimal debt settlement*. Unpublished note.
- Splitwise engineering blog — "How we split bills" (internal).
