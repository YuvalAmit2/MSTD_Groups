# Reproduce everything in this repository except the cluster runs themselves.
#
#   make            build all programs
#   make check      all consistency checks (about 5 minutes on a laptop)
#   make tables     recompute M1, M2, ... for 3 <= k <= 61 and rebuild data/*.csv (about 1 minute)
#   make clean      remove build products
#
# Needs a C compiler (gcc or clang) and Python 3.8+; `make check` also needs
# `pip install mpmath`.  Pass CFLAGS="-O3 -march=native" for full speed on x86.

CC      ?= cc
CFLAGS  ?= -O3 -funroll-loops
PYTHON  ?= python3

BIN = balanced_counts/balanced_dihedral checks/brute_dihedral checks/brute_moments ratio_check/libindep.so

all: $(BIN)

balanced_counts/balanced_dihedral: balanced_counts/balanced_dihedral.c
	$(CC) $(CFLAGS) -o $@ $<
checks/brute_dihedral: checks/brute_dihedral.c
	$(CC) $(CFLAGS) -o $@ $<
checks/brute_moments: checks/brute_moments.c
	$(CC) $(CFLAGS) -o $@ $<
ratio_check/libindep.so: ratio_check/indep.c
	$(CC) $(CFLAGS) -shared -fPIC -o $@ $<

tables: all
	@echo "== exact M1, M2, P, Q and the bound for 2^N - B, k = 3..61"
	rm -f data/moments_dihedral.jsonl
	for k in $$(seq 3 61); do $(PYTHON) ratio_check/dihedral_moments.py $$k --m2 >> data/moments_dihedral.jsonl || exit 1; done
	$(PYTHON) ratio_check/make_tables.py

check: all
	@echo "== 1. balanced-subset counter vs two brute-force programs, k = 1..12"
	@for k in $$(seq 1 12); do \
	  a=$$(balanced_counts/balanced_dihedral $$k | head -1 | sed -n 's/.*= //p'); \
	  b=$$(checks/brute_dihedral $$k | sed -n 's/.*balanced=//p'); \
	  c=$$(sed -n "s/^$$k,[0-9]*,\([0-9]*\),.*/\1/p" data/balanced_counts.csv); \
	  echo "   k=$$k counter=$$a brute=$$b table=$$c"; \
	  [ "$$a" = "$$b" ] && [ "$$a" = "$$c" ] || { echo MISMATCH; exit 1; }; done
	$(PYTHON) checks/reference_bruteforce.py | tail -3
	@echo "== 2. counter, single process, k = 13..18 vs table"
	@for k in $$(seq 13 18); do \
	  a=$$(balanced_counts/balanced_dihedral $$k | head -1 | sed -n 's/.*= //p'); \
	  c=$$(sed -n "s/^$$k,[0-9]*,\([0-9]*\),.*/\1/p" data/balanced_counts.csv); \
	  echo "   k=$$k counter=$$a table=$$c"; [ "$$a" = "$$c" ] || { echo MISMATCH; exit 1; }; done
	@echo "== 3. the sharding / re-splitting scheme used for k = 30, simulated on k = 16"
	$(PYTHON) checks/simulate_hybrid_partition.py balanced_counts/balanced_dihedral 16
	@echo "== 4. re-derive k = 18..30 from the raw cluster outputs"
	$(PYTHON) checks/recombine_raw_outputs.py
	@echo "== 5. moment formulas (Lemmas 3.5, 4.3) vs brute force over all subsets, k = 3..10"
	$(PYTHON) checks/compare_moments_bruteforce.py 3 10
	@echo "== 6. ratio table from data/moments_dihedral.jsonl"
	$(PYTHON) ratio_check/make_tables.py
	@echo "== 7. numerical claims in Sections 3-6"
	$(PYTHON) checks/paper_thresholds.py
	@echo "All checks passed."

clean:
	rm -f $(BIN)
	rm -rf data/raw/extracted

.PHONY: all tables check clean
