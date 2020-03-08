Title: Development System Setup - Edgeboard RISC-V Series
Date: 2020-2-25 12:30
Modified: 2020-2-25 12:30
Category: RISC-V
Tags: embedded, virtualization, desktop
Slug: dev-system-setup-edgeboard-series
Status: published

## Intro

This article is a part of the [Edgeboard RISC-V series]({filename}edgeboard-series.md).  Check out other articles as well if you came in through a search engine.

A developer needs a system to work with.  For embedded developers, a development system does not refer to the platform his work is going to run on (that's called the _target_), but the system he uses daily to produce the work.  This article introduces the setup of my daily driver, a [Lenovo ThinkPad T470p](https://www.lenovo.com/us/en/laptops/thinkpad/thinkpad-t-series/ThinkPad-T470p/p/22TP2TT470P) with [Intel® Core™ i7-7820HQ Processor](https://ark.intel.com/content/www/us/en/ark/products/97496/intel-core-i7-7820hq-processor-8m-cache-up-to-3-90-ghz.html) and 32GB DDR4 RAM.  Even with the same setup, your mileage may vary under different hardware configurations.

As it is quite a nuisance to write an article for every single purpose of the system, I will briefly cover all the roles of this machine, but not going into details.  As a result, this article is __not__ meant to be treated as a _system configuration guide_.

## The host operating system

After quite long struggling with Arch Linux and Gentoo, especially [with the desktop experience]({filename}/Gentoo/install-gentoo-in-hyper-v.md), I turned to the well-known Microsoft Windows operating system in 2018.  After several iterations of reinstallation, the current installation has been serving since July 2019 (confirmed via battery report of OS).  The specific system variant as of writing is shown as follows.

![winver screenshot]({static}/images/winver-20200225.png)

Note that the system is in Insiders Slow Ring to get a usable 20H1 build.  This will be explained in the following section.

The host system functions as the primary interface (i.e. captures all the keyboard and mouse input from _me_, outputs to internal and external monitors, drives all connected peripherals, provides connectivity).  Besides, it hosts almost all the complex development tools that require a GUI (e.g. VSCode, Visual Studio, IntelliJ IDEA, Vivado, IDA Pro, Intel Parallel Studio, etc.), utilities, the Chrome browser, Internet chat programs, Office and Adobe suites, as well as a little bit of leisure stuff (connects to the organization SMB share for some classical music).  [MSYS2](https://www.msys2.org/) is also installed for tasks that are largely platform agnostic but require a Unix utility to run ([example](https://github.com/chipsalliance/rocket-chip/blob/8cec10850a217d49a34d24fc3ae799daed6bcf26/src/main/scala/diplomacy/DeviceTree.scala#L135)).

## Virtualization platforms

You've seen it correct: the system has multiple virtualization platforms installed and running, namely Hyper-V and VMware Workstation.  The two platforms would not work together if you're on current versions of Windows and VMware.  According to [imbushuo](https://t.me/mm256_cmpeq_epi8), Microsoft has provided VMware with some internal APIs for VBS support.  As a result, with [VMware Workstation Tech Preview 20H1](https://blogs.vmware.com/workstation/2020/01/vmware-workstation-tech-preview-20h1.html) and [Windows 10 Insider Preview Build 19041](https://blogs.windows.com/windowsexperience/2019/12/10/announcing-windows-10-insider-preview-build-19041/), one can simultaneously enable the two platforms and boot virtual machines from both of them.  However, due to the nature of nested virtualization (VMware workstation runs in the host domain of Hyper-V), a [performance impact](https://en.wikipedia.org/wiki/Second_Level_Address_Translation) is anticipated, and VMware will hint you about this:

![vmware hint]({static}/images/vmware-nested-hint-20200225.png)

The two VM platforms host two different virtual machines, each serves different purposes.  Both of the virtual machines are accessed over SSH via [PuTTY](https://www.putty.org/).  Furthermore, home directories in the two VMs are mapped back into Windows via [SSHFS](https://github.com/libfuse/sshfs) for convenient file exchanging.

- Hyper-V hosts an Arch Linux OS.  This is currently the main development platform for Unix stuff like OCaml, Linux kernel, cross-compiling, $$\LaTeX$$, etc.  The VM is [enlightened](https://docs.microsoft.com/en-us/windows-server/administration/performance-tuning/role/hyper-v-server/terminology) for best I/O performance and memory balloon support.
- VMware Workstation hosts an Arch Linux OS.  This is for USB passthrough of the JTAG table to a Linux environment.  Hyper-V does not support USB passthrough, yet [OpenOCD](http://openocd.org/), the embedded debug translator, on Windows require [WinUSB](https://docs.microsoft.com/en-us/windows-hardware/drivers/usbcon/winusb) drivers, which is incompatible with Vivado Hardware Server.  The problem does not exist on Linux with `libusb-1.x`.

With this setup, I can run OpenOCD whenever a gdb session is needed, and switch to [hwserver](https://aur.archlinux.org/packages/xilinx-hw-server/) whenever I need to use Xilinx debug cores or program the FPGA.