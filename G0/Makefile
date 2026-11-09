# ==============================================================================
# RISC-V Bare-Metal Lockstep Co-Simulation Makefile (Checklist Item 5.1)
# ==============================================================================
# Format-Organized Project Architecture:
#   c/       : C source files (*.c)
#   asm/     : Assembly source and startup files (*.s)
#   ld/      : Linker script (*.ld)
#   rtl/     : Verilog/SystemVerilog hardware RTL (*.v, *.sv)
#   tb/      : Verilog testbench (*.v)
#   scripts/ : Verification and trace comparison scripts (*.py)
#   hex/     : Memory initialization files (*.hex, *.mem)
#   elf/     : Compiled RISC-V ELF binaries (*.elf)
#   disass/  : Disassembly files (*.disass)
#   sim/     : Simulation binaries and models (*.vvp)
#   logs/    : Execution traces and comparison reports (*.log)
#   images/  : Architecture and workflow diagrams (*.png)
# ==============================================================================

# Toolchain configuration
PREFIX       ?= riscv64-unknown-elf-
CC           := $(PREFIX)gcc
OBJCOPY      := $(PREFIX)objcopy
OBJDUMP      := $(PREFIX)objdump
NM           := $(PREFIX)nm
SPIKE        ?= /opt/riscv/bin/spike
PYTHON       ?= python3
IVERILOG     ?= iverilog
VVP          ?= vvp

# Simulation parameters
RESET_PC     := 0x80000000
MAX_CYCLES   := 50000

# Directory layout by file format
C_DIR        := c
ASM_DIR      := asm
LD_DIR       := ld
RTL_DIR      := rtl
TB_DIR       := tb
SCRIPTS_DIR  := scripts
HEX_DIR      := hex
ELF_DIR      := elf
DISASS_DIR   := disass
SIM_DIR      := sim
LOGS_DIR     := logs
IMAGES_DIR   := images

# Ensure output directories exist
_DUMMY := $(shell mkdir -p $(ELF_DIR) $(DISASS_DIR) $(HEX_DIR) $(SIM_DIR) $(LOGS_DIR))

# Target and file names
TARGET       ?= baremetal_helloworld
C_SRC        := $(C_DIR)/$(TARGET).c
ASM_START    := $(ASM_DIR)/start.s
LINKER_LD    := $(LD_DIR)/linker.ld

ELF          := $(ELF_DIR)/$(TARGET).elf
DISASS       := $(DISASS_DIR)/$(TARGET).disass
MEM          := $(HEX_DIR)/$(TARGET).mem
IMEM_HEX     := $(HEX_DIR)/imem.hex
DMEM_HEX     := $(HEX_DIR)/dmem.hex

SPIKE_LOG    := $(LOGS_DIR)/spike_$(TARGET).log
RTL_LOG      := $(LOGS_DIR)/rtl_$(TARGET).log
RTL_SIM_VVP  := $(SIM_DIR)/rtl_sim.vvp

# RTL & TB files
RTL_SRCS     := $(wildcard $(RTL_DIR)/*.v)
TB_SRC       := $(TB_DIR)/tb_top.v
COMP_SCRIPT  := $(SCRIPTS_DIR)/compare_traces.py

# ==============================================================================
# Macro: Run Lockstep Comparison and Output Appended Target Log
# ==============================================================================
define RUN_COMPARE
	@TARGET_TAG="$(strip $(1))"; \
	BASE_LOG="$(LOGS_DIR)/compare_$${TARGET_TAG}.log"; \
	echo "==> [COMPARE] Comparing Spike ISS vs RTL commit traces in lockstep..."; \
	echo "==> [COMPARE] Log: $${BASE_LOG}"; \
	$(PYTHON) $(COMP_SCRIPT) $(SPIKE_LOG) $(RTL_LOG) --start-pc=$(RESET_PC) -o "$${BASE_LOG}"
endef

# Default Target: Run full verification flow
all: check

# ------------------------------------------------------------------------------
# 1. Compile Bare-Metal Executable (ELF, Disassembly, and Memory Hex)
# ------------------------------------------------------------------------------
compile: $(ELF) $(DISASS)

$(ELF): $(ASM_START) $(C_SRC) $(LINKER_LD)
	@echo "==> [BUILD] Compiling bare-metal executable $(ELF)..."
	$(CC) -march=rv32im_zicsr -mabi=ilp32 -O0 -nostdlib -T $(LINKER_LD) $(ASM_START) $(C_SRC) -o $@

$(DISASS): $(ELF)
	@echo "==> [BUILD] Generating disassembly $(DISASS)..."
	$(OBJDUMP) -d -S $< > $@

hex: $(IMEM_HEX) $(DMEM_HEX)

# Extract instructions exclusively into imem.hex (Code only)
$(IMEM_HEX): $(ELF)
	@echo "==> [BUILD] Extracting instruction binary (code only) -> $(IMEM_HEX)..."
	$(OBJCOPY) -O verilog -j .text \
	    --verilog-data-width=4 --change-addresses=-$(RESET_PC) $< $@

# Extract constants, data, tohost, and bss exclusively into dmem.hex (No instructions)
$(DMEM_HEX): $(ELF)
	@echo "==> [BUILD] Extracting data binary (constants/data/bss) -> $(DMEM_HEX)..."
	$(OBJCOPY) -O verilog -j .rodata -j .data -j .sdata -j .tohost -j .bss -j .sbss \
	    --verilog-data-width=4 --change-addresses=-$(RESET_PC) $< $@

# ------------------------------------------------------------------------------
# 2. Run Spike Instruction Set Simulator (ISS)
# ------------------------------------------------------------------------------
spike: $(SPIKE_LOG)

$(SPIKE_LOG): $(ELF)
	@echo "==> [SPIKE] Running Spike ISS (--log-commits) on $(ELF)..."
	$(SPIKE) --isa=rv32im_zicsr --log-commits -l --log=$@ $<

# ------------------------------------------------------------------------------
# 3. Run RTL Simulation (Icarus Verilog + vvp)
# ------------------------------------------------------------------------------
rtl: $(RTL_LOG)

$(RTL_SIM_VVP): $(RTL_SRCS) $(TB_SRC)
	@echo "==> [RTL] Compiling RTL and testbench with $(IVERILOG)..."
	$(IVERILOG) -g2012 -o $@ $(RTL_SRCS) $(TB_SRC)

$(RTL_LOG): $(RTL_SIM_VVP) $(IMEM_HEX) $(DMEM_HEX) $(ELF)
	@TOHOST_ADDR=$$($(NM) $(ELF) | grep -w "tohost" | awk '{print $$1}'); \
	echo "==> [RTL] Running RTL simulation (tohost=0x$$TOHOST_ADDR, max_cycles=$(MAX_CYCLES))..."; \
	$(VVP) $(RTL_SIM_VVP) +imem_hex=$(IMEM_HEX) +dmem_hex=$(DMEM_HEX) +tohost_addr=$$TOHOST_ADDR +max_cycles=$(MAX_CYCLES) +log_file=$@

# ------------------------------------------------------------------------------
# 4. Target Execution Rules (Produces compare_<target_name>.log)
# ------------------------------------------------------------------------------
# Generic runner for any program target
run-target: $(ELF) $(DISASS) $(IMEM_HEX) $(DMEM_HEX) $(SPIKE_LOG) $(RTL_LOG)
	@$(call RUN_COMPARE,$(TARGET_TAG))

# Program-specific targets
main:
	@$(MAKE) TARGET=main TARGET_TAG=main run-target

baremetal_helloworld:
	@$(MAKE) TARGET=baremetal_helloworld TARGET_TAG=baremetal_helloworld run-target

# General check target
check: $(ELF) $(DISASS) $(IMEM_HEX) $(DMEM_HEX) $(SPIKE_LOG) $(RTL_LOG)
	@$(call RUN_COMPARE,$(if $(filter baremetal_helloworld,$(TARGET)),check,$(TARGET)_check))

# Dedicated compare target
compare: $(SPIKE_LOG) $(RTL_LOG)
	@$(call RUN_COMPARE,$(if $(filter baremetal_helloworld,$(TARGET)),compare,$(TARGET)_compare))

# ------------------------------------------------------------------------------
# 5. Fault Injection Test: Verify that a Mismatch Triggers Build Failure
# ------------------------------------------------------------------------------
test-mismatch: $(SPIKE_LOG) $(RTL_LOG) | $(LOGS_DIR)
	@echo "==> [TEST] Injected deliberate fault to verify mismatch reporting..."
	@sed 's/x1  0x80000010/x1  0xDEADBEEF/' $(RTL_LOG) > $(LOGS_DIR)/rtl_fault.log
	@TARGET_TAG="test-mismatch"; \
	BASE_LOG="$(LOGS_DIR)/compare_$${TARGET_TAG}.log"; \
	echo "==> [COMPARE] Output Log: $${BASE_LOG}"; \
	if $(PYTHON) $(COMP_SCRIPT) $(SPIKE_LOG) $(LOGS_DIR)/rtl_fault.log --start-pc=$(RESET_PC) -o "$${BASE_LOG}"; then \
		echo "ERROR: Deliberate fault went undetected!"; \
		rm -f $(LOGS_DIR)/rtl_fault.log; \
		exit 1; \
	else \
		rm -f $(LOGS_DIR)/rtl_fault.log; \
		echo "SUCCESS: Deliberate fault caught and recorded in $${BASE_LOG}!"; \
	fi

# ------------------------------------------------------------------------------
# 6. Clean Artifacts
# ------------------------------------------------------------------------------
clean:
	@echo "==> [CLEAN] Removing generated files..."
	rm -f $(ELF_DIR)/* $(DISASS_DIR)/* $(HEX_DIR)/* $(SIM_DIR)/* $(LOGS_DIR)/* *.vcd

# ------------------------------------------------------------------------------
# 7. Unit-Level Test for RV32M Accelerator
# ------------------------------------------------------------------------------
RV32M_SRCS := $(RTL_DIR)/booth_enc.v $(RTL_DIR)/pp_gen.v $(RTL_DIR)/csa.v \
              $(RTL_DIR)/rv32m_mul.v $(RTL_DIR)/rv32m_div.v $(RTL_DIR)/rv32m_unit.v
RV32M_TB   := $(TB_DIR)/tb_rv32m_unit.v

test-m-unit: $(RV32M_SRCS) $(RV32M_TB)
	@echo "==> [TEST] Compiling rv32m_unit self-checking testbench..."
	$(IVERILOG) -g2001 -o $(SIM_DIR)/tb_rv32m.vvp $(RV32M_SRCS) $(RV32M_TB)
	@echo "==> [TEST] Running rv32m_unit simulation..."
	$(VVP) $(SIM_DIR)/tb_rv32m.vvp

.PHONY: all compile hex spike rtl compare check test-mismatch main baremetal_helloworld run-target clean test-m-unit
