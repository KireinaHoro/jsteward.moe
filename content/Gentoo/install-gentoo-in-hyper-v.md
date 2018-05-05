Title: Installing Gentoo in Hyper-V
Date: 2018-05-05 00:00
Modified: 2018-05-05 00:00
Category: Gentoo
Tags: gentoo, linux, virtualization
Slug: install-gentoo-in-hyper-v
Status: published

## The story

After struggling with HiDPI issues on native GNU/Linux and battery life issues on macOS, I resorted to using Windows 10 as the main operating system on my laptop. Though there's WSL, it's not running Gentoo and has a severely degraded performance. As `crossdev` is really easy to use for building a cross-compile toolchain ([the reason that I needed a cross-compile toolchain]({filename}/GSoC 2018/weekly-report-0507.md)) with [crossdev](https://wiki.gentoo.org/wiki/Crossdev). So, I need a virtual machine running Gentoo on my Windows 10 system. This article logs the process of installing Gentoo inside Hyper-V, Windows 10's built-in hypervisor.

## Enable Hyper-V on Windows 10

First of all, we need to enable Hyper-V on our Windows 10 host. With Hyper-V, the underlying structure of Windows changes greatly; read [this](https://docs.microsoft.com/en-us/virtualization/hyper-v-on-windows/reference/hyper-v-architecture) for a detailed explanation of the Hyper-V architecture. Navigate to Control Panel -> Programs and Features -> Enable or disable Windows features (my system is in Japanese, so this maybe inaccurate; follow what's shown on your system), where you'll see an item called Hyper-V. Tick both "Hyper-V platform" and "Hyper-V management tools". Note that you'll need at least the Pro x64 version of Windows to see that "Hyper-V platform" feature. Reboot after committing the changes.

## Downloading the install ISO and creating the virtual machine

We need the minimal ISO for amd64 to install. Navigate to your favorite mirror site and pick up the ISO image in `releases/amd64/autobuilds/current-install-amd64-minimal/`. The link I used is [here](https://mirrors.tuna.tsinghua.edu.cn/gentoo/releases/amd64/autobuilds/current-install-amd64-minimal/install-amd64-minimal-20180415T214502Z.iso) (hosted by TUNA Association of Tsinghua University).

Locate and open the Hyper-V Manager on Windows (hint: use Windows Search). Create a virtual machine from Operations (right sidebar) -> New -> Virtual Machine. (Again, this may not be what's exactly displayed on the screen; follow what you see that has the most similar meanings.) Follow the wizard to create the virtual machine. When you're prompted to select the Generation of the new VM, choose Gen 1, which means BIOS boot--UEFI is an overkill here; when prompted for CD/DVD drive, choose the ISO you just downloaded. As this is a Gentoo guest, I would recommend as much RAM as possible (I gave 16GB out of a total physical RAM of 32GB--your mileage may vary). The VM should now be successfully created.

Before starting the virtual machine, we need to configure several things. Right click on the newly-created virtual machine and select Settings.

  * Select the Processor page from the left sidebar, and adjust the number of cores you wish to grant to the Gentoo guest. 
  * Select the Network page from the left sidebar, and choose the adapter type. The default switch is configured to do NAT for the virtual machine. If you want to access the virtual machine from outside the host OS, create a new Switch by selecting the Virtual Switch Manager from the right sidebar in the Hyper-V Manager main window and creating a new switch that bridges the virtual machines' NICs with the interface you choose on the host.

**NOTE:** for Gen 1 virtual machines to boot, the boot drive (virtual disk on which the OS sits) has to be an IDE drive. SCSI drives won't work as boot drives; they'll function as data drives only. Double-check your configuration to make sure that you'll install Gentoo (at least the bootloader) on an IDE drive, otherwise you'll encounter cryptic errors (such as garbled text in VM firmware).

## Boot the virtual machine and install system

Double-click on the configured virtual machine in Hyper-V Manager, then choose Start. Install Gentoo as usual ([AMD64 Handbook](https://wiki.gentoo.org/wiki/Handbook:AMD64) for reference). If the Hyper-V console was too cumbersome to use, enable sshd in LiveCD and connect to the virtual machine via XShell, PuTTY, or any SSH client of your choice. Check the VM's ip address via `ip addr`; depending on your virtual machine network configuration, you may see a NAT address (`172.17.0.0/16`) or an address from your upstream network (if in bridged mode). Connect to the address the VM got.

When configuring the kernel, note that the following options are needed for Hyper-V guest support; otherwise the kernel may not be able to find the root partition or other devices.

	CONFIG_HYPERV=y
	CONFIG_HYPERV_STORAGE=y
	CONFIG_HYPERV_NET=y
	CONFIG_HYPERV_KEYBOARD=y
	CONFIG_HYPERV_UTILS=y
	CONFIG_HYPERV_BALLOON=y
	CONFIG_FB_HYPERV=y
	CONFIG_HID_HYPERV_MOUSE=y

I prefer a minimal kernel config, to speed up build time and to reduce final kernel image size. [This](https://gist.github.com/KireinaHoro/cfa71bb97e8e893ac854407b151ae360) is the config I use, with most unneeded drivers removed.

For bootloader, I've picked LILO, as it has the `run-parts` plugin for kernel install, and LILO itself is very lightweight and easy to configure. Refer to [LILO's Gentoo Wiki page](https://wiki.gentoo.org/wiki/LILO) for information about how to install and configure.

## Bootstrap a aarch64 cross-compile toolchain

This is the point of having Gentoo as the guest OS, instead of just using Ubuntu in WSL or some other distribution. Emerge `crossdev` and build a cross-compile toolchain for `CHOST=aarch64-unknown-linux-gnu`. Note that before using crossdev, we'll need an overlay to store the modified ebuilds in. Consult [this article](https://wiki.gentoo.org/wiki/Custom_repository#Crossdev) for how to setup an overlay for `crossdev`.

	localhost / # emerge -v crossdev
	localhost / # crossdev -S -P -v -t aarch64
	
Verify that the newly-created toolchain works fine by compiling a simple "Hello, world!" program and executing it on the target machine:

	localhost ~ # cat > hello.cc << EOF
	#include <iostream>
	int main() {
		std::cout << "Hello, world!" << std::endl;
		return 0;
	}
	EOF
	localhost ~ # aarch64-unknown-linux-gnu-g++ hello.cc -o hello -static
	localhost ~ # file hello
	hello: ELF 64-bit LSB executable, ARM aarch64, version 1 (GNU/Linux), statically linked, for GNU/Linux 3.7.0, not stripped
	localhost ~ #

Transfer the `hello` executable to the target machine and see if it works.

	$ adb push hello /sdcard/
	( ... output elided ... )
	$ adb shell
	angler:/# cd /sdcard
	angler:/sdcard# ./hello
	Hello, world!
	angler:/sdcard#
