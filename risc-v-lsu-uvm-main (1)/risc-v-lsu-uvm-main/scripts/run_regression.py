#!/usr/bin/env python3
# =============================================================================
# run_regression.py — Regression runner for RV32I LSU UVM Verification Project
# Compiles once, runs all tests × seeds, parses logs, prints summary report.
# Usage: cd scripts && python3 run_regression.py
# =============================================================================

import subprocess
import os
import re
from datetime import datetime

# ── Configuration ─────────────────────────────────────────────────────────────
TESTS = [
    "lsu_smoke_test",
    "lsu_coverage_test",
    "lsu_stress_test",
    "lsu_regression_test",
]

SEEDS = [1001, 2002, 3003, 4004, 5005]

# VCS compile command
VCS_COMPILE = (
    "vcs -sverilog -ntb_opts uvm-1.2 "
    "+incdir+../tb "
    "../tb/lsu_pkg.sv "
    "../design/ls_unit.v "
    "../tb/lsu_if.sv "
    "../tb/lsu_transaction.sv "
    "../tb/lsu_driver.sv "
    "../tb/lsu_monitor.sv "
    "../tb/lsu_scoreboard.sv "
    "../tb/lsu_coverage.sv "
    "../tb/lsu_sequences.sv "
    "../tb/lsu_agent.sv "
    "../tb/lsu_env.sv "
    "../tb/lsu_tests.sv "
    "../tb/lsu_assertions.sv "
    "../tb/top_tb.sv "
    "-o simv"
)

SIM_CMD = (
    "./simv "
    "+UVM_TESTNAME={test} "
    "+ntb_random_seed={seed} "
    "+UVM_VERBOSITY=UVM_MEDIUM "
    "-l logs/{test}_{seed}.log"
)

# ── Log parser ────────────────────────────────────────────────────────────────
def parse_log(path):
    """Return (passed:bool, errors:list[str])."""
    if not os.path.exists(path):
        return False, ["Log file missing"]

    errors   = []
    all_pass = False

    with open(path) as f:
        for line in f:
            if "ALL FUNCTIONAL AND ALIGNMENT CHECKS PASSED" in line or "ALL CHECKS PASSED" in line:
                all_pass = True
            if "UVM_ERROR" in line or "UVM_FATAL" in line:
                all_pass = False
                m = re.search(r'(UVM_(?:ERROR|FATAL))\s+.*?:\s+(.*)', line)
                if m:
                    errors.append(f"{m.group(1)}: {m.group(2).strip()}")

    return all_pass, errors

# ── Helpers ───────────────────────────────────────────────────────────────────
def run(cmd):
    return subprocess.run(cmd, shell=True,
                          stdout=subprocess.DEVNULL,
                          stderr=subprocess.DEVNULL).returncode

def print_report(results):
    ts     = datetime.now().strftime("%Y-%m-%d %H:%M")
    total  = len(results)
    passed = sum(1 for v in results.values() if v[0])
    failed = total - passed

    bar = "=" * 62
    print(f"\n{bar}")
    print(f"  RV32I LSU REGRESSION REPORT   {ts}")
    print(bar)
    print(f"  Total: {total}   PASS: {passed}   FAIL: {failed}")
    print(bar)

    for test in TESTS:
        t_pass = sum(1 for s in SEEDS if results.get((test, s), (False,))[0])
        print(f"\n  [{t_pass}/{len(SEEDS)}]  {test}")
        for seed in SEEDS:
            ok, errs = results.get((test, seed), (False, ["not run"]))
            tag = "PASS" if ok else "FAIL"
            print(f"         seed={seed}  {tag}")
            for e in errs[:2]:
                print(f"           !! {e}")

    print(f"\n{bar}")
    if failed == 0:
        print("  >>> ALL RV32I LSU TESTS PASSED <<<")
    else:
        print(f"  >>> {failed} TESTS FAILED <<<")
    print(f"{bar}\n")

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    os.makedirs("logs", exist_ok=True)

    print("[1/2] Compiling RV32I ls_unit with UVM testbench...")
    if run(VCS_COMPILE) != 0:
        print("ERROR: Compilation failed. Check VCS output.")
        return

    print(f"[2/2] Running {len(TESTS)} tests × {len(SEEDS)} seeds...\n")
    results = {}

    for test in TESTS:
        for seed in SEEDS:
            cmd = SIM_CMD.format(test=test, seed=seed)
            print(f"  {test}  seed={seed}", end="  ", flush=True)
            run(cmd)
            log  = f"logs/{test}_{seed}.log"
            ok, errs = parse_log(log)
            results[(test, seed)] = (ok, errs)
            print("PASS" if ok else "FAIL")

    print_report(results)

if __name__ == "__main__":
    main()
