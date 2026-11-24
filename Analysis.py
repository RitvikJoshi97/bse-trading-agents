"""Summarise profit per session for each trader type.

Reads either:
  * final_results.csv  - written by Experiment.py (end-of-session balances), or
  * a two-column file of (trader_type, balance) rows, the format the trader
    classes append to results.csv (see results/2022_results.csv).

For each trader type it reports the number of sessions, the mean profit with
zero-profit sessions counted, and the mean profit with them removed.

2026 fix: the 2022 version hard-coded five trader types, so any other type in
the file (e.g. ARIMA) raised KeyError, and it stored averages back into its
session-count variable. Types are now discovered from the data.

Usage:
    python Analysis.py                          # final_results.csv
    python Analysis.py results/2022_results.csv
"""

import csv
import sys
from collections import defaultdict


def load(path):
    with open(path, newline="") as f:
        rows = [r for r in csv.reader(f) if r]
    if rows and rows[0][0] == "experiment":  # Experiment.py format
        header, rows = rows[0], rows[1:]
        i_exp, i_type, i_avg = header.index("experiment"), header.index("trader_type"), header.index("avg_profit")
        return [(r[i_exp].split("_")[0], r[i_type], float(r[i_avg])) for r in rows]
    return [("all", r[0], float(r[1])) for r in rows]  # legacy (type, balance)


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "final_results.csv"
    profits = defaultdict(list)
    for experiment, ttype, profit in load(path):
        profits[(experiment, ttype)].append(profit)

    print("%-6s %-10s %8s %14s %14s %8s" % ("exp", "trader", "sessions", "mean (zeros)", "mean (no 0s)", "zeros"))
    for (experiment, ttype), values in sorted(profits.items()):
        non_zero = [v for v in values if v != 0]
        mean_all = sum(values) / len(values)
        mean_nz = sum(non_zero) / len(non_zero) if non_zero else 0.0
        print("%-6s %-10s %8d %14.1f %14.1f %8d" % (experiment, ttype, len(values), mean_all, mean_nz, len(values) - len(non_zero)))


if __name__ == "__main__":
    main()
