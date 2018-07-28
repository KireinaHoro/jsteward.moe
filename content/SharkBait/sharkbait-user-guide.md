Title: SharkBait User Guide
Date: 2018-07-25 19:00
Modified: 2018-07-25 19:00
Category: SharkBait
Tags: sharkbait, android, gsoc
Slug: sharkbait-user-guide
Status: published

## Welcome to SharkBait!

This article is intended for devices that are supported by SharkBait.  The current list of supported devices is as follows:

  * Huawei Nexus 6P (`angler`)

If your device is not in the list, consult the [Porter's Guide]({filename}sharkbait-porters-guide.md) for instructions on how to add support for a device.  The rest of this article assumes that you have a device that's supported.  Let's get started!

## Install a normal Android system

The first step is to install a normal version of Android on your device.  Note that the system should have ADB root access (i.e. ability to `adb root` and get `adbd` running as root).  [Lineage OS](https://lineageos.org/) should be a good choice in many cases.

## Flash boot.img to disable full-disk encryption

The supported devices have corresponding pages that contain links to scripts that modifies the `boot.img` extracted from the device to disable forced encryption.  Clone [the SharkBait Setup repository](https://github.com/KireinaHoro/sharkbait-setup) to your work computer and do the following.

**Warning:** The following steps wipe your device's `userdata` and `cache` partition (a.k.a. "factory reset").  Make sure that important data is backed up before continuing.

```bash
cd sharkbait-setup
DEVICE=angler # substitute with your device name
sudo ./decrypt.sh $DEVICE
```

After the device has boot up, verify that the following command doesn't output anything, which indicates that forced encryption has been disabled:

```bash
adb shell mount | grep "/dev/block/dm-"
```

## Setup Gentoo chroot in /data/gnu

Gain root access via adb.  Make path `/data/gnu`; this will be the home of Gentoo root, which will become the system root soon.  Follow [Guide on Gentoo Wiki](https://wiki.gentoo.org/wiki/Handbook:AMD64/Installation/Stage) to set up the Gentoo root.  Note the following points during the setup:

  * Pick `arm64` stage3 tarballs that can be found [here](http://distfiles.gentoo.org/experimental/arm64/) instead of AMD64 stage3 tarballs;
  * Add user `portage` to gid 3003 (`inet`):
    * `groupadd -g 3003 inet && gpasswd -a portage inet`
  * Install [the proj/android.git overlay](https://gitweb.gentoo.org/proj/android.git/) that contains Android-specific kernel sources and utilities.  Refer to [Layman page on Gentoo Wiki](https://wiki.gentoo.org/wiki/Layman) for how to add an overlay to the system.
  * Choose `sys-kernel/${BOARD_NAME}-sources` instead of the general `sys-kernel/gentoo-sources` when picking the kernel source.  Install `virtual/android-sources` for packages that want the `virtual/linux-sources` virtual.  Also, install `sys-kernel/linux-headers` with exactly the same version as the sources from the overlay.
  * Install `sys-kernel/installkernel` for automatic deploying boot.img on Android.
    * Read post-installation message carefully.
  * Configure the kernel as the following:
    * Some kernels require a specific version of compiler.  Try using an older version of compiler if problems occur (e.g. compile errors, unable to boot, etc.)
    * `make sharkbait_${BOARD_NAME}_defconfig`
    * change the kernel config according to your needs
    * try your best to config as builtin instead of modules due to poor module dependency system in Android kernel source
    * `unset TMPDIR` before `make`: adb has strange environment variables that breaks build
    * **skip the installation of kernel** (**do not** `make install` yet -- `sharkbait-deploy` needs the current boot.img to deploy Android container)
  * Skip configuring the bootloader

We need LXC to run Android in a container.  The kernel sources of supported devices have necessary LXC options enabled by default.  Install `sys-apps/sharkbait-setup` and do the following:

```bash
DEVICE=angler # substitute with your device name
sudo sharkbait-deploy $DEVICE
```

## Install the kernel

Now go to `/usr/src/linux` and install the kernel:

```bash
cd /usr/src/linux
make modules_install && make install
```

## Reboot and test!

The genuine test for installing an operating system is rebooting and see if things work out as expected.  Reboot the phone the Android way: select "Reboot" in the power menu.  The phone should boot up normally.  To go back into Gentoo, "dial home" via the shell script installed at `/data/ssh/dialhome`:

```bash
adb shell
/data/ssh/dialhome
```

Join #shark-bait @ Freenode for discussion or for help in case anything goes wrong.  Also, if you have other devices that are not yet supported by SharkBait, you can help with porting them, following the [Porter's Guide]({filename}sharkbait-porters-guide.md).
