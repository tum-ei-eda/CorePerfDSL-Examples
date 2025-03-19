# CorePerfDSL-Examples
Examples of CorePerfDSL descriptions

## Models

### CV32E40P
Model of the 4-stage RISC-V CPU CV32E40P.
- Modelled instructions: RV32IM
- Static branch prediction
- No memory model

### CVA6
Model of the 6-stage RISC-V CPU CVA6.
- Modelled instructions: RV64IM
- Instructions queue (IQ) and execute stage with scoreboard
- Dual-commit
- Dynamic branch prediction
- Memory model with internal L1 instructiona and data caches

### SimpleRISCV
Custom example to illustrate flexiblity of CorePerDSL.
- 5-stage, Harvard microarchitecture
- Modelled instructions: RV32IMC
- No, static and dynamic branch prediction
- With and without data forwarding
- Dummy memory model

## Version

This is version v2.0.

This repository does not contain any submodules.