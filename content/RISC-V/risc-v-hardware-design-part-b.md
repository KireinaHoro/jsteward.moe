Title: RISC-V Hardware Design: Debug via BSCAN Chain - Edgeboard RISC-V Series
Date: 2020-2-27 13:00
Modified: 2020-2-27 15:40
Category: RISC-V
Tags: risc-v, debugging, fpga, embedded
Slug: risc-v-hardware-design-part-b-edgeboard-series
Status: published

## Intro

This article is a part of the [Edgeboard RISC-V series]({filename}edgeboard-series.md).  Check out other articles as well if you came in through a search engine.

After [setting up the hardware system]({filename}risc-v-hardware-design-part-a.md), we need a way to test if the system is actually running.  The [BootROM](https://github.com/KireinaHoro/rocket-zynqmp/tree/master/bootrom) is the location where the [reset vector](https://github.com/KireinaHoro/rocket-zynqmp/blob/master/src/main/scala/Configs.scala#L50) points to, but to change the code in the BootROM one needs to resynthesize and reimplement the design, which can take up to an hour for a Zynq UltraScale+ device on the [development system]({filename}dev-system-setup.md).  As a result, a fast, external debug method is needed, and GDB with [OpenOCD](https://github.com/riscv/riscv-openocd) satisfies this requirement perfectly.  This article covers how the BSCAN tunnel mechanism was adapted to work on Zynq UltraScale+ devices.

## BSCANE2 primitive on Xilinx devices

While it is possible to use PL GPIO and connect a separate JTAG cable to directly access the Rocket Chip JTAG TAP, but I failed to plan ahead and [had just purchased one JTAG cable]({filename}zu3eg-purchase.md), and it's too much labour to switch between the cabling of Xilinx JTAG and that of the GPIO JTAG every time I want to program a bitstream or debug RISC-V.  Fortunately, we can [find that](https://www.xilinx.com/support/documentation/sw_manuals/xilinx2018_1/ug974-vivado-ultrascale-libraries.pdf) 7 Series and UltraScale architectures provide a [BSCANE2](https://forums.xilinx.com/t5/Other-FPGA-Architecture/BSCANE2-documentation/td-p/354185) primitive:

> This design element allows access to and from internal logic by the JTAG Boundary Scan logic controller. This allows for communication between the internal running design and the dedicated JTAG pins of the device. Each instance of this design element will handle one JTAG USER instruction (USER1 through USER4) as set with the JTAG_CHAIN attribute.
> To handle all four USER instructions, instantiate four of these elements and set the JTAG_CHAIN
attribute appropriately.
> For specific information on boundary scan for an architecture, see the Configuration User
Guide for the specific device.

This indicates that we can send JTAG commands to a PL design through the user registers accessible on the PL TAP from the dedicated JTAG port of the ZynqMP chip.  The user chains, specifically `USER1` by default, powers the on-board debug facilities such as ILA, JTAG Master, or VIO:

![debug hub chain]({static}/images/debug-hub-user-chain.png)

Referring to [UG470 7 Series FPGAs Configuration User Guide](https://www.xilinx.com/support/documentation/user_guides/ug470_7Series_Config.pdf) we can find out details about advanced features of JTAG on these devices besides user chains, for example [programming a bitstream with OpenOCD from macOS](https://jiege.ch/hardware/2020/02/09/program-artix7-on-macos/).

There has already been [a mechanism](https://jiege.ch/hardware/2020/02/09/rocket-chip-bscan-analysis/) that utilizes the `USER4` chain to tunnel requests to the RISC-V TAP: [the BSCAN tunnel translator in Chisel](https://github.com/sequencer/rocket-playground/blob/master/playground/src/fpga/FPGA.scala#L39) and [the BSCAN tunnel implementation in RISC-V OpenOCD](https://github.com/riscv/riscv-openocd/blob/7cb8843794a258380b7c37509e5c693977675b2a/src/target/riscv/riscv.c#L361).  The solution will not work directly here however:

- The Zynq UltraScale+ platform uses a different JTAG IR for `USERx` chains:
    - `0x20` - `0x23` for 7-series FPGA
    - `0x920` - `0x923` for Zynq UltraScale+
    - This can be confirmed in the [BSDL Models](https://www.xilinx.com/support/download/index.html/content/xilinx/en/downloadNav/device-models/bsdl-models/zynq-ultrascale-plus-mpsoc.html) released by Xilinx
    - Addressed in OpenOCD via [commit](https://github.com/KireinaHoro/riscv-openocd/commit/cb7f6be16f56a62fc1bdafe0030862e42446e6b2)
- The Zynq UltraScale+ TAP scan chain structure is different from normal FPGAs
    - The user chains are located on the PL TAP (IR LEN=6) which is on the chain __concatenated__ with the PS TAP (IR LEN=6), resulting in a single TAP with IR LEN=12
    - There is an ARM DAP sitting between the combined PS/PL TAP and TDO, which shifts the input and output data (DR contents) by one bit (bypass), addressed in the following commits:
        - The BSCAN tunnel translator: [commit](https://github.com/KireinaHoro/rocket-zynqmp/commit/29b176484089042058a6d3fd6b22e63f9c8b32c8), [commit](https://github.com/KireinaHoro/rocket-zynqmp/commit/ce6a810722530894ff2f9f38efb6ed26386f1fb5), handles the __input delay__ of one TCK cycle due to OpenOCD TAP selection
        - OpenOCD: [commit](https://github.com/KireinaHoro/riscv-openocd/commit/11238e1eb4ecb883ee36fcf24668187c782ade5a), handles the __output delay__ of one TCK cycle due to the ARM DAP

A picture from the article [「ZYNQ UltraScale+ MPSoCのJTAGのしくみ」](http://nahitafu.cocolog-nifty.com/nahitafu/2018/10/zynq-ultrasca-1.html), which explains the JTAG structure of Zynq UltraScale+ in detail:

![zujtag]({static}/images/zujtag-nahitafu.png)

## GDB

After understanding the user chain mechanisms for Zynq UltraScale+, we can finally attach GDB to our RISC-V core.  An OpenOCD config originally for debugging the APUs (Cortex-A53) on ZynqMP was [adapted](https://github.com/KireinaHoro/rocket-zynqmp/blob/master/openocd.cfg) to enable RISC-V debugging.  Stop hardware server (to avoid `libusb` conflict with OpenOCD), launch OpenOCD, and attach gdb:

```text
(the hwserver)
# systemctl stop hwserver
# openocd -f openocd.cfg -c "init_riscv"
```

```text
(the development machine)
# riscv64-linux-gnu-gdb
...
(gdb) target remote 192.168.79.129:3333
```

The following picture shows loading an OpenSBI ELF (which will be covered in the follow-up software articles) to DDR at `0x40000000`:

![gdb load]({static}/images/gdb-load-opensbi.jpg)