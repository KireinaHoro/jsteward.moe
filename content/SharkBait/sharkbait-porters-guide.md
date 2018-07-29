Title: SharkBait Porter's Guide
Date: 2018-07-27 23:00
Modified: 2018-07-27 23:00
Category: SharkBait
Tags: sharkbait, android, gsoc
Slug: sharkbait-porters-guide
Status: published

## Welcome, porters!

This article is intended for porters who want to add SharkBait support for a device that's not currently supported.  In this article, you will be given the general idea on how to adapt parts that are crucial for SharkBait system to work on a device.  The following components will be covered:

  * Preinit.  [repository home](https://github.com/KireinaHoro/preinit)
  * SharkBait-setup. [repository home](https://github.com/KireinaHoro/sharkbait-setup)
  * Kernel sources. (`sys-kernel/${BOARD_NAME}-sources`) [example](https://github.com/KireinaHoro/android/tree/master/sys-kernel/angler-sources)
  * Kernel headers. (`sys-kernel/linux-headers-${BSP_VERSION}`) [example](https://github.com/KireinaHoro/android/tree/master/sys-kernel/liunx-headers)

## Preinit

Preinit performs early initialization of the device to load the Gentoo init (OpenRC as of current).  The following directory structure is required for a supported device (`angler` as an example here) is as follows:

```
angler
├── bootimg.cfg
├── initramfs
│   ├── init
│   └── (other contents in initramfs)
└── Makefile
```

  * `bootimg.cfg` defines offsets for kernel and initramfs, as well as kernel commandline options.  Porters should adapt what they get when dissecting `boot.img` for their device and make the following modifications:
    * remove `bootsize` option so that abootimg does not complain about a boot.img bigger than the original one (though this is unlikely to be the case).
    * add `androidboot.selinux=permissive` to the boot commandline to set SELinux to permissive.
  * `initramfs` holds the minimal initramfs that correctly mounts filesystems and `switch_root` to load Gentoo init.
    * `initramfs/init` is required.  The `angler` init is a shell script that does the necessary jobs, but any executable file should work.
    * Mind the permissions: kernel won't be able to execute an `init` that's not executable, which would result in a boot failure.
  * `Makefile` enables processing the `initramfs` programmatically before `installkernel` packs it up.
    * This will be useful for things like `busybox` installation, runtime-specific things, etc.
    * `installkernel` will call `make` in the device directory (`angler` in the directory hierarchy).  Read the example `Makefile` so that you handle the paths correctly.

## SharkBait-setup

SharkBait-setup handles the setup of the Android container.  The following directory structure is required for a supported device (`angler` as an example here) is as follows:

```
angler
├── disable_encryption.sh
├── fstab.android
├── patches
│   ├── fstab.angler.patch
│   └── (other patches to apply to Android rootfs)
└── serial-consoles (if any)
```

  * `disable_encryption.sh` is ran on the helper workstation and disables encryption for the partition where the Gentoo root will reside in.
    * For devices that does not support encryption or have the Gentoo root in a partition that's not encrypted, this script should just print a notice and return 0.
    * **Warn users about data wipe and wait for 10 seconds for a Ctrl-C!**
  * `fstab.android` is appended to the Gentoo fstab and contain mountpoints that are necessary for Android.
    * Android's `vold` should not handle any mounts any more; make sure all required mounts are present.
    * It is strongly recommended to mount to `/var/lib/android` and then bind into the LXC rootfs for ease when accessing the Android partitions and extra security.  Refer to the example `fstab.android` file for `angler` to get a better understanding of this.
  * `patches` holds patches that will be applied to the real Android rootfs via `patch -p0`, extracted from the current boot.img present on the device.
    * Disable all partition mounts in `fstab.$DEVICE.patch` or equivalent file.
    * Put more patches that are required here, such as patches on `init.rc` to properly handle cgroups issues introduced by containerization.  Refer to `init.rc.patch` for `angler` for more information on this topic.
  * `serial-consoles` defines serial consoles that are available on the device, if there is any.  This file will be appended to `/etc/inittab`.

## Kernel sources

The kernel source package of a device packages the source tree from the vendor.  A ebuild for `sys-kernel/${BOARD_NAME}-sources` is required; read the [ebuild for `angler-sources`](https://github.com/KireinaHoro/android/blob/master/sys-kernel/angler-sources/angler-sources-3.10.73.ebuild) for reference.  Only the package name, version, and the git repo URL would require adapting; the other parts of the ebuild do not need modification.

The following modifications on the source tree are required for a working kernel:

  * Apply [this patch](https://github.com/KireinaHoro/android_kernel_huawei_angler/commit/be819350157b2aadcbc8db7001119130f0e51bad.patch) on the tree to enable `installkernel` function.
  * Supply a valid `defconfig` with LXC features enabled.  See [the example for angler](https://github.com/KireinaHoro/android_kernel_huawei_angler/blob/sharkbait/arch/arm64/configs/sharkbait_angler_defconfig) and [LXC on Gentoo Wiki](https://wiki.gentoo.org/wiki/LXC#Kernel_options_required) for reference.
  * Make sure that the kernel **compiles** and **boots correctly** with (relatively) new compilers from Gentoo.
  * Regularly merge upstream changes.

## Kernel headers

Kernel headers that match the device kernel source ease the process of compiling cross-compile toolchains for Android targets.  The [ebuild for `angler`](https://github.com/KireinaHoro/android/blob/master/sys-kernel/linux-headers/linux-headers-3.10.73.ebuild) should be a clear example, with only the need to modify the version number and the git repo URL.

## Test the port

Make sure the port boots correctly.  You may need a serial console to debug boot failures.  Also, check that all the hardware functions work properly (camera, bluetooth, etc.); if that's not the case point it out when submitting a merge request so that we can look into the issue.  Happy hacking!
