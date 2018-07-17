Title: C/C++ Toolchain for Android Build on aarch64 (WIP)
Date: 2018-07-16 0:00
Modified: 2018-07-16 0:00
Category: Android
Tags: android, toolchain
Slug: toolchain-for-android
Status: published

## Disclaimer

This article is a *stub*.  This means that it may only serve status report purposes; it may contain severe scientific fallacies and/or inappropriate language, or have missing sections of information.  In case of disagreement on previous point, **cease consumption/utilization of content in this webpage immediately**.

## Preface

Many essential components in the Android platform are written in C/C++ and, apparently, toolchainss are required to build them correctly.  Google designed Android's build system to only run on `linux-x86` or `darwin-x86`, and they shipped prebuilt toolchains for only x86, `x86_64-unknown-linux-gnu` to be specific.  To build for an `arm64` device on a `x86_64` host, toolchains targeting the following [target triplets](https://wiki.osdev.org/Target_Triplet) are needed:

  * `x86_64-linux-glibc`: for compiling build tools that run on the host
  * `aarch64-linux-android`: for compiling `arm64` objects that run on the device *in 64bit*
  * `arm-linux-androideabi`: for compiling `arm` objects that run on the device *in 32bit*

All the toolchains above run on the build host (`x86_64` in a standard build).  What we need to do is to make these toolchains available on `aarch64`, while not changing the target.  Note that `x86_64-linux-glibc` produces objects for *the build host*, so it should actually be the host's native compiler: if we're building on `aarch64`, it should be something like `aarch64-unknown-linux-gnu`.

Most parts of Android uses Clang/LLVM to build as well.  We'll need the respective targets for Clang/LLVM on the `aarch64` build host as well.  We'll look into this later in this article.

## GCC part

### Host toolchain: `aarch64-unknown-linux-gnu`

This is the simplest part: Gentoo's system compiler should *just work*.  What we need to do here is to find out the "root" of the host toolchain, just like the path for the prebuilt toolchains as recorded in [`build/soong`](https://github.com/LineageOS/android_build_soong).  We can then mimic how the prebuilt x86 toolchains get registered in the build system to inject our native toolchain into the system.

### Device toolchain: `aarch64-linux-android` & `arm-linux-androideabi`

These toolchains are cross-compile toolchains that produce code for the Android platform.  The difference between these toolchains and a normal GNU/Linux toolchain for `aarch64` is that a normal toolchain uses Glibc, and the Android toolchain uses [Bionic](https://en.wikipedia.org/wiki/Bionic_(software)) for libc.  Experiments on building a Android GCC toolchain that runs on `aarch64` are being conducted at present and is still in its beginning.

## Clang/LLVM part

Clang is used to compile most of the C/C++ code in the Android platform; Google is even compiling the Linux kernel with Clang ([guide on GitHub](https://github.com/nathanchance/android-kernel-clang)), so apparently a Clang/LLVM toolchain for the Android target is necessary.  A brief description of building the clang toolchain in the AOSP source tree can be found in [this article (external)](https://hardenedlinux.github.io/toolchains/2016/04/01/How_to_build_Clang_toolchains_for_Android.html), but obviously more work is needed to build for `aarch64` hosts, and integrating the results into the Android build system for the new build host.

## Integrating the toolchains into the build system

Unfortunately, the Android system is strongly coupled with its prebuilt toolchains, and the paths for toolchains and architecture detection is littered around the repo (mainly in the build/ repositories).  Known locations of toolchain path references: (paths below are clickable)

  * [build/make/envsetup.sh](https://android.googlesource.com/platform/build/+/master/envsetup.sh)
  * [build/make/core/envsetup.mk](https://github.com/LineageOS/android_build/blob/lineage-15.1/core/envsetup.mk)
  * [build/soong/Android.bp](https://github.com/LineageOS/android_build_soong/blob/lineage-15.1/Android.bp)
  * [build/soong/cc/config/x86_linux_host.go](https://github.com/LineageOS/android_build_soong/blob/lineage-15.1/cc/config/x86_linux_host.go)

The process of integrating the toolchain configured in the sections above into the build system is a painstaking one, as Google hardly documents the intrinsic mechanisms of the gigantic, complex build system.  A series of trial-and-error attempts is expected.
