#!/usr/bin/env bash
# =============================================================================
# run_xrun.sh — Cadence Xcelium execution script for RV32I ls_unit UVM TB
# Usage: ./run_xrun.sh [test_name]
# Example: ./run_xrun.sh lsu_smoke_test
#          ./run_xrun.sh lsu_regression_test
# =============================================================================

TEST=${1:-lsu_regression_test}
SEED=${2:-1001}

echo "=== Running Cadence Xcelium for RV32I ls_unit ==="
echo "Test: ${TEST} | Seed: ${SEED}"

xrun -64bit -sv -uvm \
  +incdir+../tb \
  ../tb/lsu_pkg.sv \
  ../design/ls_unit.v \
  ../tb/lsu_if.sv \
  ../tb/lsu_transaction.sv \
  ../tb/lsu_driver.sv \
  ../tb/lsu_monitor.sv \
  ../tb/lsu_scoreboard.sv \
  ../tb/lsu_coverage.sv \
  ../tb/lsu_sequences.sv \
  ../tb/lsu_agent.sv \
  ../tb/lsu_env.sv \
  ../tb/lsu_tests.sv \
  ../tb/lsu_assertions.sv \
  ../tb/top_tb.sv \
  +UVM_TESTNAME=${TEST} \
  -svseed ${SEED} \
  +UVM_VERBOSITY=UVM_MEDIUM \
  -timescale 1ns/1ps \
  -access +rwc \
  -coverage all \
  -covoverwrite \
  -l xrun_${TEST}_${SEED}.log
