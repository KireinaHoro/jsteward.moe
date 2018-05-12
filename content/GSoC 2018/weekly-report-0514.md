Title: Gentoo GSoC Weekly Report 05/14
Date: 2018-05-12 0:00
Modified: 2018-05-12 13:00
Category: GSoC 2018
Tags: android, gentoo, gsoc
Slug: weekly-report-0514
Status: published

## Things done this week

This week was about creating a repository for an `init` program written in C/C++, testing it out, and trying to load the real init inside Gentoo root. The progress of each subproject are listed below.

### Writing a "preinit" in C/C++

I've set up [a repository][1] called `preinit_angler`, which currently implements the test function (print haiku into kernel message so that we can verify them on next boot) described in [this article][2]. Implementing the toy init is necessary is because we set up a tiny-platform that we can place other things onto it in this way: maybe password prompts for entering LUKS passphrases, or options to choose different Android snapshots. What's more, this verifies that our toolchain was really generating correctly statically-linked executables that can be directly executed by the kernel. The repository also holds the incomplete code in attempt to implement Android `cryptfs` decryption by hand.

### Attempt to decrypt Android userdata

I've ran into problems tackling the native encryption of Android: after spending a considerable amount of time on reading the code and splitting functions out from `vold`, I ran into the dead end of ARM's Trusted Execution Environment (TEE, learn more about it [here on Wikipedia][3]). The detailed process of my attempt is logged in this article: [Analysis of Android cryptfs][4].

### Bypassing Android force encryption and restructuring userdata partition

As we can't use an encrypted `userdata` for now, and encryption is forced on AOSP for Nexus 6P, we'll need to bypass the policy. The last section in [the `cryptfs` analysis article][4] ("What next?") describes how to do this. In short, we modify `vold`'s `fstab` so that `vold` won't encrypt the phone on first boot.

The next part is about "chainloading" the real, full-blown `/sbin/init`, which belongs to OpenRC. This is done in several stages:

  * mounting `userdata` partition, which holds Gentoo's real filesystem root
  * switching root into the mounted partition, executing OpenRC's init
  * launching Android's init in chroot (with jail if Android init checks if it's PID1; uses [jchroot][5])

Note that for `jchroot` to work, several namespace-related config options are needed, specifically:

	CONFIG_SYSVIPC
	CONFIG_IPC_NS
	CONFIG_PID_NS
	CONFIG_NET_NS
	CONFIG_UTS_NS
	
Failing to enable these options will result in `jchroot` (or to say, the `clone(2)`) failing with `EINVAL`.

## Current boot sequence, filesystem structure and current work status

After some discussion with UnderSampled, OxR463 and heroxbd on IRC, I feel it necessary to explain a few things here.

### Boot sequence and where we are now

The boot sequence is of the following stages:

  * bootloader loads `boot.img`, executing the kernel;
  * kernel executes `/init`, which is `preinit`, in the initramfs that came with `boot.img`;
  * `preinit` mounts `userdata` and handles mountpoints correctly, then executes Gentoo's `openrc-init`;
  * OpenRC starts, launching a service that uses `jchroot` to launch Android's init.
  
We're currently at the `preinit` stage, trying to launch OpenRC's init.

### Filesystem structure

The final filesystem structure would be like this: Gentoo root sits in `userdata` partition. The path `/var/lib/android` is special: it holds the Android `init` as well as Android mountpoints. When we `jchroot` into `/var/lib/android`, Android init would mount the partition it needs correctly, except for `/data` in the Android root. We'll need to change the `fstab` entry for `userdata` into a bind mount of `/data` (from Android's perspective of view; the real path in `userdata` is `/var/lib/android/data`) to _itself_, thus making `/data` a mountpoint, so as to make `vold` happy. 

## Work to be done next week

By the end of next week we shall see: an Android system successfully booting inside a chroot (and namespaces) under OpenRC init, who gets loaded by `preinit`. Several expected problems/projects:

  * `switch_root` into `userdata/gentoo` temporarily to see if OpenRC loads fine. Fix it if it's not working.
  * Refactor `userdata`, deal with the mountpoints correctly, and edit Android `fstab` accordingly. Android's `fstab` parser may not support bind mounts; we may have to bind-mount it ourselves and remove that line in `fstab` completely.
  * We'll definitely run into problems, thus a serial console through UART (in headphone jack for Nexus'es and Pixels) is necessary; asynchronous `console-ramoops` does not fulfill the requirement for interactions.
  
   This requires a headphone-jack UART cable, which was made by @imi415 on Telegram. Kudos for @imi415!

[1]: https://github.com/KireinaHoro/preinit_angler
[2]: {filename}replace-android-init-with-test-script.md
[3]: https://en.wikipedia.org/wiki/Trusted_execution_environment
[4]: {filename}/Android/analysis-of-android-cryptfs.md
[5]: https://github.com/vincentbernat/jchroot
