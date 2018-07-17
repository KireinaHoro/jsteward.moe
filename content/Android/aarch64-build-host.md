Title: Enabling aarch64 as a host architecture for Android Build (WIP)
Date: 2018-07-15 12:00
Modified: 2018-07-15 12:00
Category: Android
Tags: android, toolchain, build
Slug: aarch64-build-host
Status: published

## Disclaimer

This article is a *stub*.  This means that it may only serve status report purposes; it may contain severe scientific fallacies and/or inappropriate language, or have missing sections of information.  In case of disagreement on previous point, **cease consumption/utilization of content in this webpage immediately**.

## Preface

As a key step in the Portage-powered Android project, we need the ability to build Android on an `aarch64` host (not necessarily Android, as Gentoo which is beneath Android is essentially a normal aarch64 host now) so that we can build the system on the phone itself.  However, the current Android build system assumes one of the following types of build hosts:

  * Linux on AMD64
  * Darwin on AMD64

We need to add `aarch64` and `arm` (32bit variant) toolchain support into the build system.  Google originally provieded toolchain support by shipping prebuilt toolchains with the AOSP project; apparently we have to use local toolchains or build cross-compile toolchains on our own.  This article logs modifications to the AOSP build system (`${T}/build`) to accomodate system toolchain into the build system.  All source modifications can be found in my [forked repositories](https://github.com/KireinaHoro?tab=repositories), which all came from Lineage OS project originally.

# Get the build system to recognize aarch64 as a valid HOST arch

The repository [`build/make`](https://github.com/KireinaHoro/android_build) holds core makefiles that describe how the build system works.  The following code in `build/make/core/envsetup.mk` defines the `HOST_ARCH` section for the build host:

```make
# HOST_ARCH
ifneq (,$(findstring x86_64,$(UNAME)))
  HOST_ARCH := x86_64
  HOST_2ND_ARCH := x86
  HOST_IS_64_BIT := true
else
ifneq (,$(findstring i686,$(UNAME))$(findstring x86,$(UNAME)))
$(error Building on a 32-bit x86 host is not supported: $(UNAME)!)
endif
endif
```

Add `aarch64` as a host architecture and `arm` as its secondary architecture to make the build system aware that `aarch64` is a valid `HOST` for building.

## Use host Go toolchain

Google has shipped prebuilt Go toolchains for `linux-x86` and `darwin-x86`, just like they did with C/C++.  We'll use the system toolchain from Portage instead.  Emerge `dev-lang/go`, then edit the toolchain paths in [`build/soong`](https://github.com/KireinaHoro/android_build_soong), specifically `GOROOT`, to utilize the system toolchain:

### TODO: source code quote here

## Use system Ninja for building

Google shipped Ninja as well.  Emerge `dev-util/ninja` and then edit the following in [`build/blueprint`](#stub) to use system ninja:

### TODO: source code quote here

## Install Java toolchain

An Android build requires a Java toolchain to be installed.  Google does not bundle it this time: we're required to install it on the system, and the build system will try to locate it automatically at runtime.  Fortunately, Gentoo has provided a binary package (!!) for OpenJDK (`icedtea` in this case), named `dev-java/icedtea-bin`.  We just have to install this package.  To avoid unnecessary dependencies getting pulled in, configure the use flags for `dev-java/icedtea-bin` as follows:

    dev-java/icedtea-bin headless-awt -alsa -cups -gtk -webstart

Then emerge `virtual/jdk`.  More information can be found on [the Java page on Gentoo Wiki](https://wiki.gentoo.org/wiki/Java).

## Configure C/C++ toolchain

The hardest part is actually the C/C++ toolchain.  The topic is discussed in a separate article: [C/C++ Toolchain for Android Build on aarch64 (WIP)]({filename}toolchain-for-android.md).  The article briefly introduces toolchains involved in the building process.  It then describes means to get them work locally on `aarch64`.  Finally, the article describes how to accomodate the toolchains with `aarch64` as the host architecture into the Soong build system (path `build/soong/cc/config` to be specific).
