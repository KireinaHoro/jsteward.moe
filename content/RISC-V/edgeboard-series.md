Title: Series on RISC-V on the Baidu Edgeboard ZU3EG
Date: 2020-2-25 11:00
Modified: 2020-2-25 11:00
Category: RISC-V
Tags: risc-v, fpga, embedded
Slug: edgeboard-series

## Intro

I haven't been writing blog articles [ever since August, 2018](../GSoC%202018/gsoc-2018-final-report.md).  Under the strong request from [@jiegec](https://t.me/jiegec), I decided to record various related aspects of my recent works on [booting untethered, standard Linux/RISC-V on a ZynqMP board](https://github.com/KireinaHoro/rocket-zynqmp), forming a series of blog articles of which you can find links below.  The list may be updated if new, related articles come in.

## The articles

This article serves mostly as a catalog for the coming up articles.  If you're interested in _why_ the whole idea has come up, read the section that follows.

- _placeholder for the first article_

## The idea

_Note: this section has not undergone thorough fact checks and may suffer from fallacies in factual accuracy or lack references.  It is laid out here only for informative purposes._

The idea of running RISC-V on a ZynqMP dates back to 2019, when a project from [the lab I'm currently in](https://ceca.pku.edu.cn/) required an experimental platform about accelerators coupling with RISC-V.  The board we were holding at the time was a [Xilinx ZCU102](https://www.xilinx.com/products/boards-and-kits/ek-u1-zcu102-g.html).  There had been [a flow](https://github.com/li3tuo4/rc-fpga-zcu) adapted from the original work of [RocketChip on a Zynq](https://github.com/ucb-bar/fpga-zynq) from UCB.  Built around [`fesvr`, the FrontEnd SerVeR](https://github.com/riscv/riscv-fesvr), that project implemented a __tethered__ system of RISC-V tied to the ARM core in a Zynq system via AXI.  We will not cover too much the details of a `fesvr` system; briefly speaking, the RISC-V core uses DRAM from Zynq PS via AXI master port, and accepts external control via the [UCB-specific, undocumented HTIF interface](https://github.com/ucb-bar/riscv-sodor/issues/13) over an AXI slave.  This enabled various applications from ISA simulation to Linux boot.

While the idea of `fesvr` may be appealing to the academic society due to its simplicity and various features, the HTIF interface was never documented thoroughly, making it difficult to analyze and extend, let alone standardize.  The [Untethered lowRISC project](https://riscv.org/wp-content/uploads/2016/01/Wed1115-untether_wsong83.pdf) has enabled the Rocket cores to boot untethered-ly via the use of a [Berkeley Bootloader](https://github.com/riscv/riscv-pk).  However, with the standardization of Machine-mode behavior by the __RISC-V SBI specification__ and the release of the [reference OpenSBI implementation](https://github.com/riscv/opensbi), as well as the upstreaming of the GNU toolchain, U-Boot/RISC-V, and Linux/RISC-V, it's now time to follow the trend and build a new flow that adopts the standard paradigms of development on RISC-V.