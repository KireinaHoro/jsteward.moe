Title: RISC-V Software Design: Bootloader - Edgeboard RISC-V Series
Date: 2020-3-7 11:00
Modified: 2020-3-7 17:30
Category: RISC-V
Tags: risc-v, embedded, fpga
Slug: risc-v-software-design-part-a-edgeboard-series
Status: published

## Intro

This article is a part of the [Edgeboard RISC-V series]({filename}edgeboard-series.md).  Check out other articles as well if you came in through a search engine.

Following the complete of [setting up debug access]({filename}risc-v-hardware-design-part-b.md), we can finally start the configuration for the first piece of software that will run on the RISC-V platform.  The bootloader in this build consists of three parts: BootROM, OpenSBI, and U-Boot.  Linux kernel will be the payload.  

_Note that this article will not cover all of the trial-and-errors appeared during the development process; only the important parts will be explained._

## The BootROM (first stage)

Per [this config line](https://github.com/KireinaHoro/rocket-zynqmp/blob/83c4a3104a0dfad18f6b69de625f97138fec8301/src/main/scala/Configs.scala#L50), the reset vector of the generated RISC-V processor will be `0x10000`, which is located at the beginning of the BootROM which Rocket Chip generates.  The [original BootROM from Rocket Chip](https://github.com/chipsalliance/rocket-chip/tree/319b6c44450ccde38f33cd8a38dd80071a0b6528/bootrom) is simply a bootloop application: a `wfi` loop, which is anything but useful.  A [real BootROM](https://github.com/KireinaHoro/rocket-zynqmp/blob/83c4a3104a0dfad18f6b69de625f97138fec8301/bootrom/bootrom.S#L6) with some code borrowed from [the CNRV repository](https://github.com/cnrv/fpga-rocket-chip), is created, and does the following:

- Enable interrupt and probe the count of harts present on the system
- Set up BootROM stack for each hart
    - Hart 0 also sets up a mark for synchronization
- Jump to [C code](https://github.com/KireinaHoro/rocket-zynqmp/blob/83c4a3104a0dfad18f6b69de625f97138fec8301/bootrom/bootloader.c#L22)
- Harts other than 0 wait until hart 0 signals initialization done
    - Hart 0 continues initialization work
- Initialize UART
- Set up machine trap (for debugging)
- Load OpenSBI ELF from BRAM to DRAM
- Signal the rest harts, branch to start of OpenSBI

The OpenSBI ELF, with device tree (FDT) and U-Boot embedded inside as its payload, is stored in a piece of block RAM outside the Rocket Chip.  The block RAM is generated via Xilinx's [Block Memory Generator](https://www.xilinx.com/products/intellectual-property/block_memory_generator.html) IP.  Compared to using Sifive's `TLROM`, Xilinx's BMG tends to correctly infer BRAM cells, while `TLROM` usually results in significant LUTRAM usage.  The BMG IP accepts a `coe` file to initialize the memory cells and require re-synthesizing the IP to change the contents.  The `coe` file is [regenerated automatically](https://github.com/KireinaHoro/rocket-zynqmp/blob/83c4a3104a0dfad18f6b69de625f97138fec8301/bootrom/Makefile#L41) whenever the BootROM is recompiled.

## OpenSBI

SBI serves as a bootloader and firmware for a RISC-V platform: it runs in M-mode, loads further stages of S-mode bootloaders (or the OS payload), hosts M-mode traps (timer, pseudo-instruction emulation, etc.), and provides service routines (`ecall` from S-mode) to operating systems.  OpenSBI is the reference implementation of the SBI standard.  A [fork of the original OpenSBI](https://github.com/KireinaHoro/opensbi) repository contains the [platform definition for Edgeboard](https://github.com/KireinaHoro/opensbi/tree/master/platform/edgeboard), namely the initialization functions, device tree, and payload definition.  The build routine is also [slightly modified](https://github.com/KireinaHoro/opensbi/commit/f9749fee89201d65439f79d50a869bfb17428b2c) to accomodate U-Boot build routine in.

### Device tree

The [device tree](https://github.com/KireinaHoro/opensbi/blob/master/platform/edgeboard/edgeboard.dts) is based on the [DTS generated by Rocket Chip](https://github.com/chipsalliance/rocket-chip/blob/8cec10850a217d49a34d24fc3ae799daed6bcf26/src/main/scala/diplomacy/DeviceTree.scala), with the following additions to reflex peripherals outside the Rocket Chip SoC over AXI.  The DTB, embedded inside OpenSBI, will have its start address passed to the next stage (U-Boot) per [platform specification](https://www.sifive.com/blog/all-aboard-part-6-booting-a-risc-v-linux-kernel).

#### UART

Two [AXI 16550](https://www.xilinx.com/support/documentation/ip_documentation/axi_uart16550/v2_0/pg143-axi-uart16550.pdf) are present: `e0000000` (`ttyS0`) is used for RISC-V console (stdin/stdout/stderr), while `e1000000` (`ttyS1`) is connected to UART1 in Zynq's processing system for a PPP connection (will be explained in a follow-up article).

```text
axi_uart0: serial@e0000000 {
    clock-frequency = <100000000>;
    compatible = "ns16550a";
    current-speed = <115200>;
    device_type = "serial";
    interrupt-parent = <&plic>;
    interrupts = <1>;
    reg = <0xe0000000 0x10000>;
    reg-offset = <0x1000>;
    reg-shift = <2>;
};
```

Note that the `ns16550a` compatible string is used instead of `ns16550`, otherwise the FIFOs will not be enabled, resulting in input overruns.  Credit for this goes to [@imi415](https://t.me/imi415).

#### MMC SDHCI

A SDHCI controller is borrowed from Zynq PS to gain access to the SD card from RISC-V: this is used for a persistent storage to hold Linux rootfs.

```text
clk200: clk200 {
    compatible = "fixed-clock";
    #clock-cells = <0>;
    clock-frequency = <200000000>;
    u-boot,dm-pre-reloc;
};
sdhci0: mmc@ff170000 {
    u-boot,dm-pre-reloc;
    compatible = "arasan,sdhci-8.9a";
    reg = <0xff170000 0x1000>;
    clocks = <&clk200 &clk200>;
    clock-names = "clk_xin", "clk_ahb";
    interrupt-parent = <&plic>;
    interrupts = <4>;
    no-1-8-v;
    disable-wp;
};
```

The `no-1-8-v` and `disable-wp` properties are borrowed from the stock FDT in the Edgeboard BSP, to work around problematic voltage switching and lack of Write Protect detection for MicroSD cards.  The `clk200` node reflects the fixed AHB clock inside PS.

#### The "chosen" node

The "chosen" node provides some default values for software, notably U-Boot and Linux.  Note that `earlycon=sbi` signals the Linux kernel to use SBI calls for early stage printing before kernel gets a chance to initialize the serial console (they're not used forever as it is expensive to do SBI calls).

```text
chosen {
    bootargs = "earlycon=sbi root=/dev/mmcblk0p2 rootwait";
    stdout-path = "/soc/serial@e0000000:115200";
};
```

#### `timebase-frequency` property

The Linux kernel [expects](https://github.com/torvalds/linux/blob/63849c8f410717eb2e6662f3953ff674727303e7/arch/riscv/kernel/time.c#L21) the `timebase-frequency` property to be under the `/cpus` node, but Rocket Chip somehow generates the property under each CPU core (e.g. `/cpus/cpu@0`), and this mismatch will result in an early panic.  The property is moved to the correct location.

### Physical Memory Protection (PMP)

The default [PMP](https://content.riscv.org/wp-content/uploads/2017/05/riscv-privileged-v1.10.pdf) initialization of current OpenSBI is not suitable for our setup: the whole firmware will be masked totally inaccessible from S-mode and U-mode, but we have our device tree embedded inside OpenSBI.  [A patch](https://github.com/KireinaHoro/opensbi/commit/dc68ecd5c2b82bd431bb138412d5607acf0cd98b) lifts the limitation to read-only firmware; in this way, the DTB will be readable by the following U-Boot payload, and will then be relocated to somewhere else in DRAM.

## U-Boot

A [U-Boot fork](https://github.com/KireinaHoro/u-boot/tree/e1b6a8fa1e65915eedb0f31cf88cbefdf7fa45e7) has been created containing the board definition of the platform, along with a minimal `defconfig`.  A [special environment variable](https://github.com/KireinaHoro/u-boot/commit/e1b6a8fa1e65915eedb0f31cf88cbefdf7fa45e7#diff-bfdb6fca569d48da8315b5565b4d99d7R17) needs to be set prior to booting a Linux kernel to prevent erroneous device tree relocation.  Credit for this goes to [@Icenowy](https://t.me/Icenowy).

After putting things together, as well as correctly setting up PS (described in a follow-up article), the BootROM prompt, OpenSBI information, and U-Boot prompt shall appear in order on the serial console.