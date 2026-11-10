# RISC-V RV32I LSU UVM Verification Environment

UVM 1.2 Verification Environment for the **RV32I Load/Store Unit** (`ls_unit.v` from the G0 core).

## Project Structure

```
risc-v-lsu-uvm-main/
├── design/
│   └── ls_unit.v            # User's RV32I Load/Store Unit RTL (DUT)
├── tb/
│   ├── lsu_pkg.sv            # RV32I memory op enums, funct3 encodings, parameters
│   ├── lsu_if.sv             # Interface bundling core pipeline & memory bridge busses
│   ├── lsu_transaction.sv    # Sequence item with RV32I instructions & golden predictors
│   ├── lsu_driver.sv         # Drives CPU pipeline inputs + emulates memory bridge
│   ├── lsu_monitor.sv        # Reconstructs transactions from memory requests
│   ├── lsu_scoreboard.sv     # Verifies req/we, address, strobes, shifting, extensions
│   ├── lsu_coverage.sv       # Functional coverage (all 8 instructions, offsets, strobes, signs)
│   ├── lsu_sequences.sv      # Seven stimulus sequences (smoke, all-ops, offsets, signs, stalls)
│   ├── lsu_agent.sv          # UVM Agent (Driver + Sequencer + Monitor)
│   ├── lsu_env.sv            # UVM Environment (Agent → Scoreboard + Coverage)
│   ├── lsu_tests.sv          # Test library (smoke, coverage, stress, regression)
│   ├── lsu_assertions.sv     # SVA protocol checkers & invariant assertions
│   └── top_tb.sv             # Top-level TB instantiating DUT & interface
└── scripts/
    ├── compile.do             # Questa / ModelSim script
    ├── run_xrun.sh            # Cadence Xcelium execution script
    └── run_regression.py      # Automated Python regression runner
```

## RTL Module Interface (`ls_unit.v`)

```
                           ┌─────────────────────────── ls_unit ────────────────────────────┐
                           │                                                                │
    core_addr[31:0] ───────┼─► mem_addr[31:0] (direct pass-through)                         │
                           │   └─► [1:0] byte_offset                                        │
                           │             │                                                  │
    lsunit[4:0] ───────────┼─► Control Unpacker                                             │
                           │     ├─► is_ls_valid ────────► mem_req                          │
                           │     ├─► is_store_op ────────► mem_we                           │
                           │     ├─► is_load_op                                             │
                           │     └─► ls_funct3[2:0]                                         │
                           │             │                                                  │
    core_wdata[31:0] ──────┼─────────────┴─► [Store Alignment & Strobe Unit]                │
                           │                   ├─► mem_wdata[31:0] (shifted per offset)     │
                           │                   └─► mem_be[3:0] (SB: 1-hot, SH: 2-hot, SW)   │
                           │                                                                │
    mem_rdata[31:0] ───────┼─────────────┬─► [Load Data Formatting Unit]                    │
                           │             │     (LB/LBU/LH/LHU slicing + sign/zero extend)   │
                           │             └───────────────► core_rdata[31:0]                 │
                           │                                                                │
    mem_stall ─────────────┼───► AND (with mem_req) ─────► core_stall                       │
    mem_err ───────────────┼───► Passthrough ────────────► core_err                         │
                           └────────────────────────────────────────────────────────────────┘
```

## Verification Scope

| Check | Description |
|---|---|
| **Control Decoding** | `mem_req == lsunit[4]`, `mem_we == (lsunit[4] & lsunit[3])` |
| **Address Passthrough** | `mem_addr == core_addr` |
| **Store Byte Strobes** | `SB` → 1-hot mask at offset (`0001`, `0010`, `0100`, `1000`), `SH` → 2-hot (`0011`, `1100`), `SW` → `1111` |
| **Store Alignment** | Barrel shifting `core_wdata << (offset * 8)` for byte/halfword stores |
| **Load Slicing & Sign Extension** | `LB` / `LH` correctly sign-extended, `LBU` / `LHU` correctly zero-extended, `LW` 32-bit pass-through |
| **Handshake & Errors** | `core_stall == (mem_req & mem_stall)`, `core_err == mem_err` |

## Test Suite

| Test Name | Description |
|---|---|
| `lsu_smoke_test` | Basic sanity check running 20 Word read/write operations |
| `lsu_coverage_test` | Exhaustive sequence hitting all 8 instructions, all offsets, and both positive/negative sign-extension |
| `lsu_stress_test` | Back-to-back operations with random back-pressure stalls (`mem_stall`) |
| `lsu_regression_test` | Complete comprehensive verification suite combining all directed and random sequences |

## Running the Verification

### 1. Cadence Xcelium (`xrun`)
```bash
cd scripts
export PATH=/home/install/XCELIUM2409/tools/bin:$PATH
export LM_LICENSE_FILE=5280@14.139.1.126
./run_xrun.sh lsu_regression_test      # or lsu_smoke_test etc.
```
All artifacts (log, `xcelium.d`, `cov_work`, waves) are written to
`scripts/sim/<test>_<seed>/`. Clean everything with `./run_xrun.sh clean`.

