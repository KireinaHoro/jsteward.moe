Title: Replace Android init with test script
Date: 2018-05-05 13:00
Modified: 2018-05-05 13:00
Category: GSoC 2018
Tags: android, gsoc
Slug: replace-android-init-with-test-script
Status: published

## Preface

As a part of my GSoC 2018 project, I'll replace Android's init with one of the init systems from GNU/Linux (OpenRC to be exact), and I've been experimenting with replacing the holy PID1 on an Android system pretty long ago (dating back to 2015), though things didn't work out at that time. According to [this article](http://whiteboard.ping.se/Android/Debian), replacing init is quite straightforward: one just throw in busybox along with a script named `init`, placed at the root of the initramfs, along with a suitable `busybox` binary. This article logs how I achieved this goal.

## Placing a hook inside Android Build System

I've added a hook to manipulate the Android root (the filesystem mounted at /) before it gets packed by `mkbootfs`, a tool for packing `ramdisk.img` in the build process. The hook can be found [here](https://github.com/KireinaHoro/android_build/commit/03ec95b81d1678d2d81b30d796a129e805ff4203), and I'm going to edit the script that the hook calls in order to really edit the initramfs. The new contents of the script look like this:

	#!/bin/bash
	echo ===== Ramdisk patch started on $(date) ===== >> ~/patch_ramdisk.log
	cp -Rv ~/new_ramdisk/* $@ >> ~/patch_ramdisk.log
	echo ===== Ramdisk successfully patched ===== >> ~/patch_ramdisk.log

Note that this script shouldn't have any output to `stdout`, as its output gets parsed by the build system as commands; writing log directly to `stdout` would result in a build failure. We should now place the new contents of our initramfs at `~/new_ramdisk`, and its contents will get added to the final ramdisk, overriding whatever is in place.

## How to tell if the new init successfully gets executed

This was a hard one. As we're not chainloading the Android init at this phase (it's a little bit complicated to figure out the mounts), we'll get a kernel panic right after whatever's done in our <del>fake </del>init. I thought about drawing something to the screen or activating the taptic engine in the beginning, so that we really know if the init gets executed. Yet, after in-depth discussions with @imbushuo and @Icenowy on Telegram, I realized that this was beyond my capabilities: Qualcomm's framebuffer devices require special operations to access them instead of directly reading from and writing to the device node at `/dev/graphics/fb0` (the internal display). I've tried to read the relevant parts of code from [MultiROM](https://github.com/Tasssadar/multirom), yet the code was complicated and doesn't compile well in my environment. The taptic engine should be something attached via GPIO on the PMIC, and we should be able to access it by writing to SPMI addresses, and, according to @imbushuo, this should be an easy task. Unfortunately, I failed to find anything useful after digging around in Nexus 6P (MSM8994)'s kernel source, and no device nodes in `/dev` look like the correct node either.

The `ramoops` debug facility in Android kernels came to the rescue. According to [this in AOSP source](https://android.googlesource.com/kernel/common/+/android-3.18/Documentation/ramoops.txt):

> Ramoops is an oops/panic logger that writes its logs to RAM before the system crashes. It works by logging oopses and panics in a circular buffer.

The path `/sys/fs/pstore/console-ramoops` stores the kernel message buffer (also known as `dmesg`) from last kernel boot, regardless of whether the boot has succeeded, crashed (kernel panic), or the power source was cut when the system was still running (in which case the kernel may not have time to write logs back to storage). In addition, we can write to `dmesg` by writing to `/dev/kmsg`; and we can get a working `/dev/kmsg` by mounting a `devtmpfs`, when nothing has been populated yet in the new root. In this way, our new init can be made like this:

	#!/sbin/bb
	
	# write log to kmsg
	log() {
	echo new_era: $@ > /dev/kmsg
	}
	
	# set up psuedo-filesystems
	mount -t devtmpfs devtmpfs /dev
	
	# write the haiku
	log Old pond
	log Frog jumps in
	log Sound of water
	log -- Matsuo Basho
	
	# sleep for a while
	sleep 10

Get a statically-linked busybox for aarch64, and put it under `sbin/` in the new ramdisk. Structure the initramfs so that it looks like the following:

	jsteward@yuki:~/new_ramdisk$ ls -l *
	-rwxr-xr-x 1 jsteward jsteward  261 May  4 02:48 init

	dev:
	total 0

	proc:
	total 0

	sbin:
	total 1764
	lrwxrwxrwx 1 jsteward jsteward       7 May  4 02:49 bb -> busybox
	-rwxr-xr-x 1 jsteward jsteward 1805928 May  4 00:42 busybox
	lrwxrwxrwx 1 jsteward jsteward       7 May  4 02:49 mount -> busybox
	lrwxrwxrwx 1 jsteward jsteward       7 May  4 02:49 reboot -> busybox
	lrwxrwxrwx 1 jsteward jsteward       7 May  4 02:49 sleep -> busybox
	jsteward@yuki:~/new_ramdisk$

And, build AOSP again, and take `out/target/product/angler/boot.img`. Reboot the phone into fastboot mode, and issue the following to let it boot the new `boot.img`:

	jsteward@yuki:~$ fastboot boot boot.img
	( ... output elided ... )
	
The phone should load the new kernel and initramfs (it's slow--be patient) and reboot in approximately 30 seconds. When it boots back into Android, we can then check `/sys/fs/pstore/console-ramoops` to see if our haiku got in there:

	jsteward@yuki:~$ adb root
	restarting adbd as root
	jsteward@yuki:~$ adb shell
	angler:/# grep -A2 new_era /sys/fs/pstore/console-ramoops
	[   12.474410] new_era: Old pond
	[   12.478773] new_era: Frog jumps in
	[   12.492715] new_era: Sound of water
	[   12.496127] new_era: -- Matsuo Basho
	[   22.520767] Kernel panic - not syncing: Attempted to kill init! exitcode=0x00000000
	[   22.520767]
	angler:/#
	
Note the 10 second delay in `dmesg`: that's when our init is sleeping for 10 seconds; kernel panics right away when init dies, which was the expected behavior--a real init should never die.

## File permissions in ramdisk

I was stuck with kernel couldn't execute my init in my first few attempts. The log looked like this:

	[   11.984835] Failed to execute /init
	[   11.988149] Kernel panic - not syncing: No init (further output elided...)
	
And, thanks to the help from @Icenowy, I discovered that the problem was I didn't put `busybox` in `/sbin` in the first time, and the build system didn't give it the executable bit in the ramdisk (despite that it had the executable bit in the working folder). As [the source](https://android.googlesource.com/platform/system/core/+/master/libcutils/fs_config.cpp#194) states, `init*` are in the permission set `AID_ROOT`, and `sbin/*` are in the permission set `AID_SHELL`. Both permission sets have the executable bit, so placing `busybox` in `sbin/` should solve the problem, and it did solve the problem.
