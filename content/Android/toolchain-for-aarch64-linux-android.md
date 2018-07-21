Title: Building a toolchain for aarch64-linux-android
Date: 2018-07-21 1:00
Modified: 2018-07-21 1:00
Category: Android
Tags: android, toolchain, gsoc
Slug: toolchain-for-aarch64-linux-android
Status: published

## Preface

To build the Android Platform, we need a toolchain that can produce executables that link correctly against Android's `libc`, Bionic.  To achieve this, a toolchain targeting `aarch64-linux-android` (and `arm-linux-androideabi`) is needed.  This article aims to provide a step-by-step guide for reproducing the desired toolchain on all architecture that GCC supports running on, including AArch64, which my GSoC project needs.  Unfinished work on this topic is documented at the end of this article.

## Step 0 -- Clone source and set up environment variables

Clone the following repositories which hold Google's modifications to the GCC toolchain for Android target:

  * [Binutils](https://android.googlesource.com/toolchain/binutils)
  * [Bionic](https://android.googlesource.com/platform/bionic)
  * [GCC](https://android.googlesource.com/toolchain/binutils)

The rest of this article assumes that `$PWD` is in the corresponding project for each step.

Export the environment variables to get the paths right:

```bash
export TARGET=aarch64-linux-android
export PREFIX=/usr/local/$TARGET
```

## Step 1 -- Build and install binutils

Binutils that can process binaries for the target is needed.  Create a separate build directory, configure, compile, and then install for target:

```bash
mkdir build && cd build
../binutils-2.27/configure --target=$TARGET --prefix=$PREFIX --enable-werror=no
make -j8 && sudo make install
```

The `--enable-werror=no` option is used to work around failed compiles due to newer versions of GCC generating new warnings.  Examine `$PREFIX` and see if the binutils for the target has been properly installed.

## Step 2 -- Install prebuilt libc & headers

The next step, as most cross-compiler creation guides instructs, is to install libc.  Unfortunately, we have not figured out a proper way to compile Bionic without Android's (gigantic) build system, so we're just doing a voodoo copy-and-paste.  The libc part in this section is expected to get better when we develop a mature solution for building Bionic.

Install `sys-kernel/linux-headers-3.10.73` from [here](https://github.com/KireinaHoro/android/tree/master/sys-kernel/linux-headers).  Set up libc and kernel headers.

```bash
sudo emerge -av =sys-kernel/linux-headers-3.10.73
mkdir -p $PREFIX/$TARGET/sys-include
cp -Rv bionic/libc/include/* $PREFIX/$TARGET/sys-include/
for a in linux asm asm-generic; do
    ln -s /usr/include/$a $PREFIX/$TARGET/sys-include/
done
```

The following object files are needed for a successful generation of the toolchain:

  * `crtbegin_so.o`: from NDK
  * `crtend_so.o`: from NDK
  * `crtbegin_dynamic.o`: from NDK
  * `crtend_android.o`: from NDK
  * `libc.so`: from AOSP
  * `libm.so`: from AOSP
  * `libdl.so`: from AOSP
  * `ld-android.so`: from AOSP

Obtain the above files and place them under `$PREFIX/$TARGET/lib` for discovery by the linker.

## Step 3 -- Build and install GCC

The final part is relatively simple.  Just compile GCC and install it into the toolchain prefix:

```bash
mkdir build && cd build
../gcc-4.9/configure --target=$TARGET --prefix=$PREFIX --without-headers --with-gnu-as --with-gnu-ld --enable-languages=c,c++
make -j8 && sudo make install
```

## Step 4 -- Build and verify "Hello, world!"

We need to verify that the toolchain is really working by creating executables for our target.  Write a simple "Hello, world!" program and compile it with:

    aarch64-linux-android-g++ hello.cc -o hello -pie -static-libgcc -nostdinc++ -I/usr/local/aarch64-linux-android/include/c++/v1 -nodefaultlibs -lc -lm -lc++

Explanation for the commandline options used:

  * `-pie`: Android requires [Position Independent Executables](https://en.wikipedia.org/wiki/Position-independent_code) property for dynamically-linked executables.
  * `-static-libgcc`: Android platform does not have `libgcc_s.so` available; we'll have to make it statically-linked.
  * `-nostdinc++` and `-I...`: Android uses `libc++` as its default STL implementation, and we need this to get the right symbols used by including right C++ headers.
    * This suggests that a correct copy of `libcxx` headers should be present at the path shown above.
  * `-nodefaultlibs` and `-l...`: by default GCC links to `libstdc++`, which is not desirable in this case; we manually specify what to consider during the linking process.
    * This suggests that `libc++.so` should be present in the linker search path.

## What else?

The work is not finished yet on this topic:

  * We still copy-and-paste `libc` object files instead of properly building them separately.  Proper packaging of `bionic` is needed.
  * The toolchain build process needs integrating with `crossdev`, Gentoo's flexible cross-compile toolchain generator.
