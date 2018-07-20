Title: Gentoo GSoC Weekly Report 07/23
Date: 2018-07-22 0:00
Modified: 2018-07-22 0:00
Category: GSoC 2018
Tags: android, gentoo, gsoc
Slug: weekly-report-0723

## Summary

I continue to work on toolchains for `-android` and `-androideabi` targets in the past week.  The following articles summarize the work done:

  * [Building a toolchain for aarch64-linux-android]({filename}/Android/toolchain-for-aarch64-linux-android.md) describes how to build a toolchain for target `aarch64-linux-android` and compile **dynamically linked** executables that run on Android platform.

The final evaluation of GSoC is nearing, and I will begin the work on the final report for evaluation, merging my work in `android.git`, and tidying up blog posts to post on the Gentoo Wiki.  Things planned that are not finished yet:

  * Bionic build without AOSP tree
  * Package GCC toolchain for Android (or integrate into crossdev; requires Bionic properly handled)
  * Clang/LLVM toolchain for Android target without AOSP tree (on AArch64)
  * AOSP build on AArch64 (with toolchain drop-in or directly use system toolchain)
  * Per-component build (implemented by Android build system already; requires native build on AArch64 done to start)

This checklist may go beyond GSoC time span, but let's hope that the end of GSoC doesn't mark the end of Portage-powered Android project.  Also, please don't hesitate to contact me if you want to help (and are not sure where to start), don't hesitate to contact me!  You can reach me by the means in my [Contact Page]({filename}/pages/about-and-contact.md).
