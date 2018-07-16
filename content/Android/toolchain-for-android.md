Title: C/C++ Toolchain for Android Build on aarch64 (WIP)
Date: 2018-07-16 0:00
Modified: 2018-07-16 0:00
Category: Android
Tags: android, toolchain
Slug: toolchain-for-android

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

## Clang/LLVM part
