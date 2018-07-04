Title: Integrating Android kernel source into Portage
Date: 2018-07-05 2:00
Modified: 2018-07-05 3:30
Category: Gentoo
Tags: gentoo, android, gsoc
Slug: android-kernel-source-portage
Status: published

## Introduction

The Linux kernel is the most important component on any systems that are based on it, be it Gentoo Linux or Android.  The user may want to tweak the kernel to enable functions that userspace utilities need (e.g. LVM, FUSE, Netfilter, etc.), so being able to tweak the configurations and install a new version easily is important.  Android's kernel, however, defaults to a pretty locked-down version with few standard Linux features besides the ones that Android needs on by default, and the kernel is tied with the initramfs into an Android-specific format called a `boot.img`.  This article introduces how Linux kernel compiling and installation works on normal Gentoo Linux systems; then it documents how `preinit`, a custom `installkernel`, as well as the device-specific `${DEVICE}-sources` (`angler-sources` in case of Nexus 6P) works together; finally, it describes how to port other devices' kernel sources using the same model.

## On a normal system

On a normal Gentoo Linux system, `sys-kernel/*-sources` holds the kernel sources, each variant with some differences (mostly in patchsets): `gentoo-sources` is officially supported by the Gentoo Kernel Team, while `ck-sources` includes Cons Koliva's kernel patchset.  The source tree gets installed to `/usr/src/linux-*`, which then gets symlink'ed to `/usr/src/linux`.  The user can install multiple kernel source trees on the system at the same time, while the active `/usr/src/linux` symlink is maintained by the `kernel` module of `eselect`.

To compile and install a kernel, the user first picks a suitable kernel source package, then goto `/usr/src/linux` and tweak options as he would with `make menuconfig` or other means.  He then builds the kernel and installs it via `make install`, which calls `/sbin/installkernel` provided by `sys-apps/debianutils[kernel_linux]`.  `installkernel` installs the produced kernel to `/boot` along with the kernel config and `System.map`, perserving the last kernel as a backup.  Finally, it runs `run-parts`, which is also from `sys-apps/debianutils`, to run any post-install hooks (e.g. LILO entry update).

## On a Portage-powered Android system

The Android kernel sources are no different in form factor from normal kernel sources: they have the same build system with normal Linux kernels; the only difference is that `make install` should work differently than regular Linux systems: Android phones expect `boot.img` in the boot partition instead of kernel images in `/boot`.  In order to satisfy this requirement, the following plan that consists of three components is developed:

  * [`sys-kernel/preinit`](https://github.com/KireinaHoro/preinit): offers device-specific initramfs files and `boot.img` parameters (kernel & initramfs offsets and boot commandline)
  * [`sys-kernel/installkernel`](https://github.com/KireinaHoro/installkernel): installs the correct kernel image (with dtb on ARM) to `/boot`, creates `boot.img`, and flashing it to the correct partition
  * [`sys-kernel/${DEVICE}-sources`](https://github.com/KireinaHoro/android_kernel_huawei_angler): kernel source with necessary patches and `defconfig` to work on a Portage-powered system
  
Preinit offers an `eselect` module for choosing the device's model.  The package's `pkg_postinst` will try to detect the current device via `androidboot.hardware` value in `/proc/cmdline`; if it failed to get a match, the user would have to manually select a device for the `preinit` files, or use the `custom` device (in which the user manually implement the preinit files).
  
The above three components have their ebuilds available [in the `sys-kernel` category in this overlay](https://github.com/KireinaHoro/android/tree/master/sys-kernel).  Add the overlay and emerge `sys-kernel/${DEVICE}-sources`; Portage will automatically pull in the dependencies.  After that, one can install kernel just like on a Linux system:

```bash
$ cd /usr/src/linux
$ make ${DEFCONFIG} && make -j$(($(nproc)+1))
$ sudo make modules_install
$ sudo make install
```
	
The `boot.img` will be automatically created and flashed to the boot partition.

## Porting guide

To add new device support to this framework, the following work needs to be done:

  * Preinit:
	* Implement a minimal initramfs, with a `/init` that mounts the necessary filesystems and launches OpenRC `init`.  Implement the initramfs building logic (e.g. busybox symlinking) in a `Makefile`.
	* Dissect existing `boot.img` for the device with `abootimg`, producing a `bootimg.cfg`. Remove the `bootsize` parameter so that `abootimg` doesn't complain when the new image is bigger.
	  * [This example for angler](https://github.com/KireinaHoro/preinit/tree/master/devices/angler) should guide you through the port.
  * `${DEVICE}-sources`:
	* Create a `defconfig` that is LXC-capable.  Refer to [the previous blog]({filename}/Android/building-lxc-ready-kernel.md) for details.
	* Apply [this patch](https://github.com/KireinaHoro/android_kernel_huawei_angler/commit/be819350157b2aadcbc8db7001119130f0e51bad?diff=unified) on the kernel sources.  This is needed to enable our custom `installkernel`.
	* Create `sys-kernel/${DEVICE}-sources` ebuild.  Follow [this](https://github.com/KireinaHoro/android/blob/master/sys-kernel/angler-sources/angler-sources-3.10.73.ebuild) as an example.
