Title: Gentoo GSoC Weekly Report 07/16
Date: 2018-07-16 5:00
Modified: 2018-07-16 5:00
Category: GSoC 2018
Tags: android, gentoo, gsoc
Slug: weekly-report-0716

## Summary

This week is mainly about decoupling toolchain from Android Build System so as to enable a local build of Android on the phone itself.  Toolchains for the following programming languages are needed throughout the entire build:

  * C/C++ (Android Platform)
  * Java (Android Platform, apps)
  * Go (build system, i.e. Soong & Blueprint)

As of current, the entire source tree is mounted onto the phone via NFS.  Tweak kernel config to enable NFS, emerge `net-fs/nfs-utils`, then mount the filesystem.  Refer to `nfs(5)` for more information.  The articles in this report assume that the AOSP tree is mounted at `/import/lineageos`.

The last week's work sums up into the following two articles:

  * [Enabling aarch64 as a host architecture for Android Build (WIP)]({filename}/Android/aarch64-build-host.md): logs modifications made to accomodate system toolchains for `aarch64` into the build system.
    * This is necessary as Google doesn't provide prebuilt toolchains for `aarch64` hosts; the build system assumes `x86` here and there as well.
  * [Using distcc to speed up builds on phone]({filename}/Gentoo/distcc-speed-up.md): speed up Portage builds on phone with `distccd` running on the laptop.
  * [C/C++ Toolchain for Android Build on aarch64 (WIP)]({filename}/Android/toolchain-for-android.md): attempt to get the set of toolchains for building Android on aarch64.

Currently there are some blocking obstacles, and I'm trying to figure out how to work around them.  They are discussed in details in the articles above.
