Title: Buidling a LXC-ready Android kernel with Gentoo toolchain
Date: 2018-05-26 10:00
Modified: 2018-05-26 13:00
Category: Android
Tags: android, linux, kernel, gentoo
Slug: building-lxc-ready-kernel
Status: published

## Preface

To run LXC, we need a kernel that has the options required by LXC on.  This article shows how to build an Android kernel that has the required options on, built by Gentoo's latest stable cross-compile toolchain built by `crossdev`.

## Install Cross-Compile Toolchain

We'll use [crossdev](https://wiki.gentoo.org/wiki/Crossdev), a set of wrapper scripts that provides cross-compilation capability to Portage.  The following instructions assume that the workstation is a Gentoo machine.

First, install `sys-devel/crossdev`:

	emerge -av sys-devel/crossdev
	
Install the latest stable toolchain:

	crossdev --stable -t aarch64-unknown-linux-gnu
	
## Clone the kernel sources and compile

The kernel source repository for Nexus 6P with my patches for compiling with GCC 6 as well as LXC-enabled config is at [`KireinaHoro/android_kernel_huawei_angler`](https://github.com/KireinaHoro/android_kernel_huawei_angler). Clone this repository and compile the kernel:

	git clone https://github.com/KireinaHoro/android_kernel_huawei_angler
	cd android_kernel_huawei_angler
	make sharkbait_angler_defconfig
	make -j8
	
The target kernel image will be available at `arch/arm64/Image.gz-dtb`.  Copy this to the `preinit` repository to continue following [Starting Android in LXC]({filename}starting-android-in-lxc.md) to build the `preinit` `boot.img`.

## Notes

Linux kernel's `make savedefconfig` doesn't really save a working `defconfig`, at least it's not the case for Android kernels.  When changes are made to `.config` (via `make menuconfig` or so), __copy `.config` back to `arch/arm64/configs`__ instead of relying on the `savedefconfig` target, otherwise you may encounter problems such as missing drivers or things that should be built-in turned out to be built as a module.

GCC 6 support was accomplished by introducing [`compiler-gcc6.h` from SaberMod/android-kernel-lge-hammerhead on GitLab](https://gitlab.com/SaberMod/android-kernel-lge-hammerhead/blob/4a98feebe2cb735eef2299bc5512b9c83cc789ce/include/linux/compiler-gcc6.h).  A few fixes regarding the `static inline` behavior change since GCC 6 has been made to make the source compile without problem.  Warning checks in `gcc-wrapper.py` was disabled as well.
