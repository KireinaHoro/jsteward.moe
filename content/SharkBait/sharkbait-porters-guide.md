Title: SharkBait Porter's Guide
Date: 2018-07-27 23:00
Modified: 2018-07-27 23:00
Category: SharkBait
Tags: sharkbait, android, gsoc
Slug: sharkbait-porters-guide

## Welcome, porters!

This article is intended for porters who want to add SharkBait support for a device that's not currently supported.  In this article, you will be given the general idea on how to adapt parts that are crucial for SharkBait system to work on a device.  The following components will be covered:

  * Preinit.  [repository home](https://github.com/KireinaHoro/preinit)
  * SharkBait-setup. [repository home](https://github.com/KireinaHoro/sharkbait-setup)
  * Kernel sources. (`sys-kernel/${BOARD_NAME}-sources`)
  * Kernel headers. (`sys-kernel/linux-headers-${BSP_VERSION}`)

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

*WIP*
