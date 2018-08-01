Title: Portage-powered Android: Gentoo GSoC 2018 Final Report
Date: 2018-08-02 8:00
Modified: 2018-08-02 8:00
Category: GSoC 2018
Tags: gsoc, gentoo
Slug: gsoc-2018-final-report

## Overview

The project is still being worked on.  Due to overly-optimistic estimation of the time needed to work on the Android build system, not all the objectives originally planned in the proposal have been finished.  The project itself, however, is going pretty smoothly and the work is expected to continue despite the finish of the GSoC program.

## Boot Gentoo system on Android hardware -- Preinit

This part is based on the work of [the Gentoo ARM64 Project](https://wiki.gentoo.org/wiki/Project:ARM64) with modifications to the boot sequence to properly boot on Android hardware.  Due to the nature of a fixed bootloader for Android, the project [Preinit](https://github.com/KireinaHoro/preinit) is created to handle early mount operations and launch Gentoo init with the embedded initramfs inside Android's in-house `boot.img` format.  Designed to adapt the difference between various Android hardware, the project is extensible and easy to add support for new devices.  An eselect module is offered for users to switch between device profiles or use their custom initramfs.

## Manage device kernel sources and headers with Portage

Android devices use kernel sources that are heavily patched to drive the vendor-specific devices, and in most situations these patches will never be submitted to the main Linux kernel source tree.  As a result, it is crucial to use the kernel source tree dedicated to the device.  Ebuilds have been created in category `sys-kernel` in the [proj/android.git](https://gitweb.gentoo.org/proj/android.git/) overlay.

Due to differences between the Android bootloader and regular bootloaders for GNU/Linux systems, a plugin to the kernel build system, [installkernel](https://github.com/KireinaHoro/installkernel), which serves to correctly install the kernel automatically, has been created.  Installkernel packs the kernel and preinit files into a `boot.img` and flashes it to the correct partition.

Using the Android kernel headers matter when building Android components natively on the device.  Ebuilds for kernel headers with version corresponding to the kernel sources have been created in the `sys-kernel` category as well, and the user is recommended to use the correct version of kernel headers.

## Start Android in container for phone functionality

The Android system is started as a guest in LXC in Gentoo.  As the Android filesystem structure differs from GNU/Linux greatly and some paths overlap, keeping the Android filesystem tree in a separate place is desired rather than mixing them together.  The project [SharkBait-setup](https://github.com/KireinaHoro/installkernel) has been created to automatically set up a vanilla Android device with Gentoo chroot available as a Portage-powered Android system.

## Toolchain for Android system target

Toolchains that run on different host architectures is important for building Android system natively on the device.  [GCC](https://jsteward.moe/toolchain-for-aarch64-linux-android.html) and [LLVM](https://jsteward.moe/toolchain-clang-llvm-with-sanitiazers-for-android.html) cross-compile toolchains for Android `aarch64-linux-android` target have been reproduced without Google's obscured scripts, which greatly helps to building Android on an AArch64 host, specifically the Android device itself.

## Separating Android build logic from the repository

The build logic for AOSP targets is described in `Android.mk` and `Android.bp` files, which gets parsed and executed by the [`android_build`](https://github.com/LineageOS/android_build) and [`android_build_soong`](https://github.com/LineageOS/android_build_soong) systems.  The two systems get separated from the AOSP repositories, which will ease the process of modular builds managed by Portage.

## Documentation Work


