Title: Gentoo GSoC Weekly Report 07/23
Date: 2018-07-22 0:00
Modified: 2018-07-22 0:00
Category: GSoC 2018
Tags: android, gentoo, gsoc
Slug: weekly-report-0723
Status: published

## Summary

I continued to work on toolchains for `-android` and `-androideabi` targets in the past week.  The following articles summarize the work done:

  * [Building a toolchain for aarch64-linux-android]({filename}/Android/toolchain-for-aarch64-linux-android.md) describes how to build a toolchain for target `aarch64-linux-android` and compile **dynamically linked** executables that run on **unmodified** Android platform.
  * [Bootstrap aarch64-linux-android Clang/LLVM toolchain](https://gist.github.com/KireinaHoro/282f6c1fef8b155126aaeb0acccf4280) is a shell script that creates a working Clang/LLVM toolchain that cross-compiles for Android target.

The final evaluation of GSoC is nearing, and I will begin the work on the final report for evaluation, merging my work in `android.git`, and tidying up blog posts to post on the Gentoo Wiki.  Things planned that are not finished yet:

  * Bionic build (and ebuilds) without AOSP tree
  * Ebuilds for GCC toolchain for Android (or integrate into crossdev; requires Bionic to be properly handled)
  * AOSP build on AArch64 (with toolchain drop-in or directly use system toolchain)
  * Per-component build (implemented by Android build system already; requires native build on AArch64 done to start)

This checklist may go beyond GSoC 2018 time span, but I hope that the end of GSoC doesn't mark the end of the Portage-powered Android project.  Also, please don't hesitate to contact me if you want to help (and are not sure where to start)!  You can reach me by the means in my [Contact Page]({filename}/pages/about-and-contact.md).

Besides the ongoing development of building Android on AArch64 host and dissecting AOSP, I am starting to work on wrap-up articles that provide steps that users (well, not *end users*) as well as porters can follow to reproduce existing work easier.  The following articles are planned:

  * Set up Portage-powered Android -- User Guide
  * Add a new device -- Porter's Guide
