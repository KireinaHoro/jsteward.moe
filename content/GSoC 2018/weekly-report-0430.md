Title: Gentoo GSoC Weekly Report 04/30
Date: 2018-04-30 12:00
Modified: 2018-04-30 12:00
Category: GSoC 2018
Tags: android, gentoo, gsoc
Slug: weekly-report-0430

## Preface

According to the schedule planned in the proposal, this week was about getting familiar with Lineage OS building process and install it on the development device. This blog post summarizes the problems I ran into (and successfully fixed) in the process, and makes a brief plan about what will be done in the following week.

## Work done this week

### Setting up working environment

The working environemnt I'm currently using is of two parts:

  * laptop running Windows / macOS for flashing the ROM package onto device
  * server running Linux for building and editting sources
  
For connection to fastboot environment, I had to install the Android USB drivers provided by Google available for download [here][1].

The build machine I use runs Ubuntu 16.04.3, which does not require much configuration. After pulling the Lineage OS source tree, I was able to complete a build according to the build instructions given by [Lineage OS wiki][2].

### Modifying kernel tree in Lineage OS build system

The workflow introduced in this section is for integrating the process of building kernel into the process of building the entire Android system. Compiling the kernel separately (i.e. configuring the cross-compile toolchain manually) will not require this specific workflow.

The kernel tree for the device I'm using for development (Nexus 6P, codename `angler`) has its kernel sources stored at 

	kernel/huawei/angler

A correct workflow for the changes to the kernel source to be considered when building the entire Android system via `brunch angler` requires one to commit changes he made; otherwise the build process will fail, complaining that the work tree is not clean. To clean the kernel repository, execute the following command:

	croot && cd kernel/huawei/angler && git clean -xfd
	
To modify the kernel configuration properly, one need to start with one of the `defconfig`s that define devices, located in

	${KERNEL_SOURCE}/arch/${ARCH}/configs/${BOARD_NAME}_defconfig

In this specific case, the configuration I use is

	${KERNEL_SOURCE}/arch/arm64/configs/lineageos_angler_defconfig
	
One can issue `make ${BOARD_NAME}_defconfig` followed by `make menuconfig` to customize the kernel configurations. To build the kernel with the configuration tailored to one's needs, he copies the generated `.config` file to override the `defconfig` he picks. Though the generated `.config` file will be far longer than the `defconfig` file, which exactly defines what's needed for the board's functionality, the configuration generated this way will work as well. The Android build system then picks the configuration up for the device to build the kernel. Note that cleaning the repository is required, as stated above.

Some compile errors (such as missing semi-colons and `#include`'s) pop up as I enable options in kernel config. <del>(This clearly demonstrates Google's poor code quality :/ )</del> I've forked the kernel repository [on GitHub][4] to store my changes to the kernel source.

### Flashing the compiled ROM package onto the device

I've been using Lineage OS before I switched over to Android Beta since the release of Oreo, so TWRP is present on the device. Yet, due to unknown reasons, the updater binary of Lineage OS ROM package had trouble identifying my device as an `angler` device correctly. It kept reporting:

	This package is for "angler" devices; this is a .
	
The issue was later resolved by flashing the newest version of TWRP (version 3.2.1-0 for `angler` at the time of writing).

Another problem is that the old system (the Android Beta Program build) has encrypted the `userdata` partition with LUKS, resulting in the recovery and the newly-installed system consistently asking for a password to decrypt the partition. As formatting the `userdata` partition after decrypting the partition in recovery only formats the `ext4` filesystem, which was _on top of_ the LUKS partition, I had to wipe the LUKS header in the partition manually in recovery as instructed [here][3]. The key is to execute the following in recovery shell:

	dd if=/dev/zero of=/dev/block/platform/soc.0/f9824900.sdhci/by-name/userdata bs=4096 count=512

Make sure that the partition (block device specified after `of=`) is the correct one. Accidentally wiping critical partitions (e.g. partitions that store the bootloader) can result in a __HARD BRICK__ which would require Qualcomm's tools to repair, which will be an extremely complicated process.

### Explorations in the Android Build System

After <del>ripgrep'ing</del>examining the AOSP source tree, I've discovered the following information that will be useful for further progress:

  * source code for Android init in `system/core/init/`; written in C++
  * packed initramfs image `ramdisk.img` (gzip-compressed cpio archive, without kernel) in `out/target/product/angler/ramdisk.img`
  * source directory for packing the initramfs in `boot.img` in `out/target/product/angler/root/`
  * Makefile for generating the `ninja` rules responsible for packing initramfs at `build/make/core/Makefile`
  
I've added a hook to the Makefile above, which runs before the image gets packed (by the tool `mkbootimg`), while after the contents of the initramfs get populated. The hook is a bash script at `build/make/core/pre_ramdisk_hook.sh`. The forked `android_build` repository is [here][5], and the related commit is [03ec95b][6].

### Android persistent store (previously known as last_kmg)

Android had a place to store the kernel message buffer for view on the next boot, which is useful for debugging boot failures. The location for the store used to be `/proc/last_kmsg`, but it has changed to the following location:

	/sys/fs/pstore/console-ramoops
	
## Plans for next week

The next week should be about getting a stage3 onto the Nexus 6P. As the current stage3 tarballs for `arm` looks quite outdated (20161129), I expect that some efforts will be needed to roll it up to match the most up-to-date portage tree.

Another plan is to write a small test program that makes some noise (e.g. printing something to dmesg, firing up the motor engine, or draw something on the screen) upon being executed. By replacing Android init with this program, we can check if home-brewed executables can be ran properly.


[1]: https://developer.android.com/studio/run/win-usb
[2]: https://wiki.lineageos.org/devices/angler/build
[3]: https://android.stackexchange.com/questions/98228/removing-encryption-from-recovery
[4]: https://github.com/KireinaHoro/android_kernel_huawei_angler/tree/tweak-config
[5]: https://github.com/KireinaHoro/android_build/tree/ramdisk-hook
[6]: https://github.com/KireinaHoro/android_build/commit/03ec95b81d1678d2d81b30d796a129e805ff4203
