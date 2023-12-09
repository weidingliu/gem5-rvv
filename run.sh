#!/bin/bash

for file in
./build/RISCV/gem5.opt ./configs/deprecated/example/se.py --cpu-type=RiscvO3CPU --caches --cmd ~/riscv-vector-tests/out/v256x64user/bin/stage2/vse8.v-0
