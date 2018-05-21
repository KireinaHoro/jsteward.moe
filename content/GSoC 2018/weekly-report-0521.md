Title: Gentoo GSoC Weekly Report 05/21
Date: 2018-05-21 19:00
Modified: 2018-05-21 19:00
Category: GSoC 2018
Tags: android, gentoo, gsoc
Slug: weekly-report-0521
Status: published

## Things done this week

Due to having to take an exam in Algebra last Friday, I revised for the test this week and didn't have much progress in GSoC this week.  This article sums up what I've tried to achieve in the past week.

## Makefile to unpack and repack boot.img without AOSP source tree

As I'm starting to hack on Android's `boot.img`, I'd be frequently unpacking and repacking it, making the old way of patching the initramfs during the AOSP build very inconvenient (a simple repack would require sourcing Android Build System's thousands of Makefiles).  I created rules for unpacking and repacking `boot.img`: the relevant changes can be found in [this commit](https://github.com/KireinaHoro/preinit_angler/commit/292d47323a74c3faa2e17f6f2dfa459278af1559#diff-b67911656ef5d18c4ae36cb6741b7965). The dependencies are as follows:

  * abootimg (for parsing `boot.img` and dissecting it according to the offsets)
  * gzip, gunzip (for unzipping compressed kernel and initcpio)
  * GNU cpio version 2.12 or newer (for handling cpio archive; 2.12 is necessary as older versions don't have the `-D` option)

### Pitfall on SELinux

Unfortunately, using the above rules to unpack and then repack the cpio archive would result in the new `boot.img` not bootable. SELinux is denying `init` to restore SELinux contexts, causing it to exit for "Security error". Seems like Android's `cpio` implementation `mkbootfs` is somehow different from GNU cpio, and can store SELinux contexts in the cpio archive, but I failed to prove this (the [sources](https://android.googlesource.com/platform/system/core/+/master/cpio/mkbootfs.c) for `mkbootfs` looks innocent).  The fix would be switching `androidboot.selinux=enforcing` to `permissive` in the kernel command line, so that `init` can finish restoring the contexts and finish boot.

## Ubuntu Touch container architecture

When browsing through articles related to Android and Linux working together, I ran into this article: [Touch/ContainerArchitecture - Ubuntu Wiki](https://wiki.ubuntu.com/Touch/ContainerArchitecture).  That was actually what I'm planning about the relationship between Gentoo and Android--Android inside a container in Gentoo, except that in Ubuntu Touch, Android serves as the HAL, while in my project Android can still do whatever it want freely (of course inside its own space).  A detailed explanation can be found in the "Filesystem Structure" section in [last week's report]({filename}weekly-report-0514.md).

## Plans for next week

The next week should be about bringing Gentoo up and launching Android inside it. I've been doing some experiments this weekend about UART and launching OpenRC's `init`, and I'm running into problems.  The results should fit into next week's report.
