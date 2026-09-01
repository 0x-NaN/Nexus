"""
burst_test.py — Measure burst detection catch rate.

Creates/reuses a dedicated test agent with a very high spend cap (so the
spend-cap rule never fires) and a configured rate_limit (so ONLY burst
detection can deny). Injects N bursts via POST /simulator/inject, then queries
the Docker Postgres for how many bursts were caught.

The backend + DB run in Docker. Injection goes to localhost:8000 (docker
backend); results are read from the docker postgres container.

Usage: python burst_test.py --count 50
"""
import argparse
import subprocess
import time
import requests

API = "http://localhost:8000"
PSQL_AGENT_CMD = ["docker", "exec", "amex_streetcode-postgres-1",
                  "psql", "-U", "postgres", "-d", "killswitch", "-t", "-A"]
ENV = {"PGPASSWORD": "postgres"}


def psql(sql):
    proc = subprocess.run(PSQL_AGENT_CMD + ["-c", sql],
                          capture_output=True, text=True, env=ENV,
                          encoding="utf-8", errors="replace")
    return proc.stdout.strip()


def resolve_test_agent():
    """Return the id of the dedicated burst-test agent (reuse or create)."""
    rows = psql("SELECT id FROM agents WHERE category='bursttest' ORDER BY id LIMIT 1")
    if rows.strip():
        return rows.splitlines()[0].strip()
    body = {
        "name": "Burst Test Agent",
        "category": "bursttest",
        "spend_cap": 1000000.00,
        "rate_limit": 5,
        "normal_range_min": 5.0,
        "normal_range_max": 50.0,
    }
    r = requests.post(f"{API}/agents", json=body, timeout=10)
    r.raise_for_status()
    return r.json()["id"]


def inject_burst(agent_id):
    body = {"agent_id": agent_id, "misbehavior_type": "burst"}
    r = requests.post(f"{API}/simulator/inject", json=body, timeout=30)
    r.raise_for_status()
    return r.json()


def run_test(n):
    agent_id = resolve_test_agent()
    print(f"\n{'='*64}")
    print(f"  BURST DETECTION MEASUREMENT — {n} injections")
    print(f"  Target agent: {agent_id} (rate_limit=5, spend_cap $1M)")
    print(f"{'='*64}\n")

    start = psql("SELECT NOW()")
    print(f"  Query window starts at: {start}\n")

    for i in range(n):
        try:
            resp = inject_burst(agent_id)
            n_txs = len(resp.get("injected", []))
            print(f"  [{i+1:3d}/{n}] injected {n_txs} txs")
        except Exception as e:
            print(f"  [{i+1:3d}/{n}] ERROR: {e}")
        time.sleep(6)

    print(f"\n  Waiting 10s for all transactions to settle...")
    time.sleep(10)

    q = f"""
WITH burst_txs AS (
    SELECT id, agent_id, decision, reason, timestamp
    FROM transactions
    WHERE misbehavior_type = 'burst'
      AND is_injected_misbehavior = TRUE
      AND agent_id = '{agent_id}'
      AND timestamp >= '{start}'
    ORDER BY timestamp
),
gaps AS (
    SELECT timestamp, decision, reason,
           (timestamp - LAG(timestamp, 1, timestamp)
               OVER (ORDER BY timestamp)) > interval '5 seconds' AS new_run
    FROM burst_txs
),
runs AS (
    SELECT timestamp, decision, reason,
           SUM(CASE WHEN new_run THEN 1 ELSE 0 END)
               OVER (ORDER BY timestamp) AS run_id
    FROM gaps
)
SELECT run_id, COUNT(*) AS tx_count,
       COUNT(*) FILTER (WHERE decision='denied' AND reason='burst_limit_exceeded') AS caught
FROM runs
GROUP BY run_id
ORDER BY run_id
"""
    lines = [l for l in psql(q).splitlines() if l.strip()]
    print(f"\n  {'Burst#':<8} {'TXs':<8} {'Denied(burst)':<15} {'Caught'}")
    print(f"  {'-'*52}")
    parsed = []
    for line in lines:
        parts = line.split("|")
        if len(parts) != 3:
            continue
        run_id, tx_count, caught = parts[0].strip(), int(parts[1].strip()), int(parts[2].strip())
        parsed.append((run_id, tx_count, caught))
        print(f"  {run_id:<8} {tx_count:<8} {caught:<15} {'YES' if caught > 0 else 'NO'}")

    total = len(parsed)
    caught_total = sum(1 for (_, _, c) in parsed if c > 0)
    pct = (caught_total / total * 100) if total else 0.0

    print(f"\n{'='*64}")
    print(f"  RESULT: Caught {caught_total}/{total} bursts ({pct:.1f}%)")
    print(f"{'='*64}\n")
    return total, caught_total, pct


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", "-n", type=int, default=50)
    args = parser.parse_args()
    run_test(args.count)
