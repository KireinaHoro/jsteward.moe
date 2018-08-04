Title: Portage-powered Android: Gentoo GSoC 2018 Final Report
Date: 2018-08-02 8:00
Modified: 2018-08-02 8:00
Category: GSoC 2018
Tags: gsoc, gentoo
Slug: gsoc-2018-final-report
Status: published

## Overview

The project is still being worked on.  Due to overly-optimistic estimation of the time needed to work on the Android build system, not all the objectives originally planned in the proposal have been finished.  The project itself, however, is going pretty smoothly and the work is expected to continue despite the finish of the GSoC program.

## Boot Gentoo system on Android hardware -- Preinit

This part is based on the work of [the Gentoo ARM64 Project](https://wiki.gentoo.org/wiki/Project:ARM64) with modifications to the boot sequence to properly boot on Android hardware.  Due to the nature of a fixed bootloader for Android, the project [Preinit](https://github.com/KireinaHoro/preinit) is created to handle early mount operations and launch Gentoo init with the embedded initramfs inside Android's in-house `boot.img` format.  Designed to adapt the difference between various Android hardware, the project is extensible and easy to add support for new devices.  An eselect module is offered for users to switch between device profiles or use their custom initramfs.

## Manage device kernel sources and headers with Portage

Android devices use kernel sources that are heavily patched to drive the vendor-specific devices, and the patches may never be submitted to the main Linux kernel source tree.  Consequently, it is crucial to use the kernel source tree dedicated to the device.  Ebuilds have been created in category `sys-kernel` in the [proj/android.git](https://gitweb.gentoo.org/proj/android.git/) overlay.

Due to differences between the Android bootloader and regular bootloaders for GNU/Linux systems, a plugin to the kernel build system, [installkernel](https://github.com/KireinaHoro/installkernel), which serves to correctly install the kernel automatically, has been created.  Installkernel packs the kernel and preinit files into a `boot.img` and flashes it to the correct partition.

Using the Android kernel headers matter when building Android components natively on the device.  Ebuilds for kernel headers with version corresponding to the kernel sources have been created in the `sys-kernel` category as well, and the user is recommended to use the correct version of kernel headers.

## Start Android in container for phone functionality

The Android system is started as a guest in LXC in Gentoo.  As the Android filesystem structure differs from GNU/Linux greatly and some paths overlap, keeping the Android filesystem tree in a separate place is desired rather than mixing them together.  The project [SharkBait-setup](https://github.com/KireinaHoro/installkernel) has been created to automatically set up a vanilla Android device with Gentoo chroot available as a Portage-powered Android system.

## Toolchain for Android system target

Toolchains that run on different host architectures is important for building Android system natively on the device.  [GCC](https://jsteward.moe/toolchain-for-aarch64-linux-android.html) and [LLVM](https://jsteward.moe/toolchain-clang-llvm-with-sanitiazers-for-android.html) cross-compile toolchains for Android `aarch64-linux-android` target have been reproduced without Google's obscured scripts, which greatly helps to building Android on an AArch64 host, specifically the Android device itself.

## Documentation Work

Development details have been kept by blog articles that explain work done on specific topics.  These articles form the weekly reports of progress.  The [user guide](https://wiki.gentoo.org/wiki/User:Jsteward/SharkBait_User_Guide) and [porter's guide](https://wiki.gentoo.org/wiki/User:Jsteward/SharkBait_User_Guide) have been created on Gentoo Wiki to serve as official documentations for the project.

## Community Building

Regular discussion about the project takes place every Saturday at 2:00 AM UTC time in #shark-bait at Freenode IRC.  Tyson Tan, the designer for the KDE mascot, have created a mascot and a logo for the project.  A website [shark-bait.org](https://www.shark-bait.org/) that serves as a portal and development blog has been created by my fellow developers that helped me work on the project.

## Work left to be done

The GSoC period is somewhat short for a massive project to restructure Android like this, and many of the things that were originally planned are not finished yet.  They will eventually get handled as the project evolves.

### Binary artifacts in the toolchain

As a sensible way to build Bionic separately has not been worked out yet, the `libc` components in the toolchains created are copied from a live Android system.  Proper build method of Bionic is required to eliminate copying object files in creating the toolchain.

### Android Build system

The manually-created toolchains have to be plugged into the Android build system to enable native building on AArch64.  Many parts of the build system currently do not make clear distinction between host OS and architecture, assuming that the host to be an x86 system.  Work is needed to rework these parts and enable the use of system toolchains instead of prebuilt ones.

### Dependency relationship between AOSP modules

The AOSP sources are modularized and support incremental, reproducible building of the modules, but the dependency relationship between modules are implicit and dynamically resolved by the build system during build.  To separately build modules, the dependency relationship needs to be clear so that the dependencies are not built multiple times.

### Eclass for Android build system functions

The Android build systems expose functions to build modules.  The functions should be wrapped in a eclass to provide a consistent interface for ebuilds for Android components.

### Support for more devices

Currently, the Portage-powered Android project only supports two devices: Huawei Nexus 6P and ASUS ZenPhone.  Support for more and newer devices is needed.

## Projects created during GSoC 2018

  * [Preinit](https://github.com/KireinaHoro/preinit)
  * [Installkernel](https://github.com/KireinaHoro/installkernel)
  * [SharkBait-setup](https://github.com/KireinaHoro/sharkbait-setup)

## Code and documentation merged upstream

  * [Commits in proj/gentoo.git](https://gitweb.gentoo.org/proj/android.git/log/)
  * Pages on Gentoo Wiki:
    * [Starting Android in LXC](https://wiki.gentoo.org/wiki/User:Jsteward/Starting_Android_in_LXC)
    * [Building a toolchain for aarch64-linux-android](https://wiki.gentoo.org/wiki/User:Jsteward/Building_a_toolchain_for_aarch64-linux-android)
    * [Clang/LLVM toolchain with sanitizers support for Android](https://wiki.gentoo.org/wiki/User:Jsteward/Clang_toolchain_with_sanitizers_support_for_Android)
    * [SharkBait User Guide](https://wiki.gentoo.org/wiki/User:Jsteward/SharkBait_User_Guide)
    * [SharkBait Porter's Guide](https://wiki.gentoo.org/wiki/User:Jsteward/SharkBait_Porter%27s_Guide)

## GSoC reports archive

[Category GSoC 2018](https://jsteward.moe/category/gsoc-2018.html)

## Acknowledgement

I appreciate the guidance from my mentor Benda Xu very much.  He shows great passion and enthusiasm in my project while still gives me great freedom to determine how the project would go when issues occur.  His extreme patience and timely help ensured the success of my GSoC 2018 project.

Stephen Christie and Lucas Ramage actively participated in the weekly discussion that takes place in the #shark-bait channel, maintain the project website, and providing crucial insights when I run into tough issues.  Stephen also contacted the artist, Tyson Tan, who created the KDE mascot, to create a logo and a mascot for the project.  Thanks a lot.  Also, I would like to show my gratefulness for Tyson for creating the cute, lovely mascot Mako.  She exactly represents what we imagined about her.

I would also like to thank the Tsinghua University TUNA Association and its energetic members for providing me with a high-quality environment to make technical discussions.  Many times when I was stuck with a problem we heatedly discuss, and complicated issues get resolved easily.

Finally, thanks to all the people who have encouraged, commented on, or criticized on my project.  Hope that my effort can make Android and Gentoo better platforms, and even better, the world a better place.
