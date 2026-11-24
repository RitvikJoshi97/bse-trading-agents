"""Run the two experiments described in the coursework report.

RECONSTRUCTED IN 2026. The original Experiment.py from 2022 was lost. This
script rebuilds it from the report (docs/) and from the experiment set-up
left commented out at the bottom of BSE.py:

  * market: symmetric supply and demand, limit prices 50-150, customer orders
    replenished every 30 s with 'drip-poisson' timing
  * Experiment 1: each agent on its own, against 10 Shaver, 10 ZIC and 10 ZIP
    traders on each side of the market
  * Experiment 2: all five agents together, against the same 30-per-side mix
  * 6 sessions of 600 s per run

Each agent trades as a BUYER. The report says agents act as buyers and
sellers, but the 2022 pricing logic of the ARIMA, SARIMAX and LSTM agents is
written for bids only: as a seller it quotes below its limit price and BSE
stops the session with 'Bad ask'. The original experiments therefore almost
certainly ran the agents on the buy side, so this reconstruction does too.
See "Known issues" in README.md.

Final balances are taken from BSE's own end-of-session summary (trade_stats),
and written to final_results.csv. The trader classes also still append a
mid-session balance to results.csv, exactly as the 2022 code did (see
"Known issues" in README.md).

Usage:
    python Experiment.py                 # both experiments, 6 x 600 s
    python Experiment.py --quick         # smoke test: 1 x 60 s session
    python Experiment.py --experiment 1 --sessions 3 --duration 300
"""

import argparse
import csv
import os
import random

import matplotlib

matplotlib.use("Agg")  # BSE imports pyplot; never open a window

import BSE  # noqa: E402

AGENTS = ["FARIMA", "FARIMASTM", "SARIMAX", "LSTM", "SGD"]
BACKGROUND = [("SHVR", 10), ("ZIC", 10), ("ZIP", 10)]


def order_schedule(start, end):
    supply = [{"from": start, "to": end, "ranges": [(50, 150)], "stepmode": "fixed"}]
    demand = [{"from": start, "to": end, "ranges": [(50, 150)], "stepmode": "fixed"}]
    return {"sup": supply, "dem": demand, "interval": 30, "timemode": "drip-poisson"}


def parse_summary(line):
    """Parse one trade_stats line into {trader_type: (total, n, average)}.

    Format: sess_id, time, best_bid, best_ask, then groups of
    (type, total_profit, n, average_profit), then best_bid, best_ask again.
    """
    fields = [f.strip() for f in line.strip().strip(",").split(",")]
    groups = fields[4:-2]
    out = {}
    for i in range(0, len(groups) - 3, 4):
        ttype, total, n, avg = groups[i : i + 4]
        out[ttype] = (int(total), int(n), float(avg))
    return out


def run(name, agents, sessions, duration, writer, seed):
    traders_spec = {"buyers": BACKGROUND + [(a, 1) for a in agents], "sellers": list(BACKGROUND)}
    summary_file = "%s_summary.csv" % name
    for s in range(1, sessions + 1):
        random.seed(seed + s)
        sess_id = "%s_sess%02d" % (name, s)
        with open(summary_file, "a") as tdump:
            BSE.market_session(sess_id, 0.0, float(duration), traders_spec,
                               order_schedule(0.0, float(duration)), tdump, False, False)
        with open(summary_file) as f:
            last = f.readlines()[-1]
        for ttype, (total, n, avg) in sorted(parse_summary(last).items()):
            writer.writerow([name, s, ttype, n, total, "%.2f" % avg])
            print("%s  %-9s n=%-2d total=%-5d avg=%.2f" % (sess_id, ttype, n, total, avg))


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--experiment", choices=["1", "2", "all"], default="all")
    p.add_argument("--sessions", type=int, default=6)
    p.add_argument("--duration", type=int, default=600, help="session length in simulated seconds")
    p.add_argument("--agents", nargs="+", default=AGENTS, choices=AGENTS)
    p.add_argument("--seed", type=int, default=2022)
    p.add_argument("--quick", action="store_true", help="1 session of 60 s, for a smoke test")
    args = p.parse_args()
    if args.quick:
        args.sessions, args.duration = 1, 60

    new_file = not os.path.exists("final_results.csv")
    with open("final_results.csv", "a", newline="") as f:
        writer = csv.writer(f)
        if new_file:
            writer.writerow(["experiment", "session", "trader_type", "n", "total_profit", "avg_profit"])
        if args.experiment in ("1", "all"):
            for agent in args.agents:
                run("exp1_%s" % agent, [agent], args.sessions, args.duration, writer, args.seed)
                f.flush()
        if args.experiment in ("2", "all"):
            run("exp2_all", args.agents, args.sessions, args.duration, writer, args.seed)


if __name__ == "__main__":
    main()
