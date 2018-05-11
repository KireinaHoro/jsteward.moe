Title: Gentoo GSoC Weekly Report 05/14
Date: 2018-05-12 0:00
Modified: 2018-05-12 0:00
Category: GSoC 2018
Tags: android, gentoo, gsoc
Slug: weekly-report-0514

## Things done this week

This week was about creating a repository for an `init` program written in C/C++, testing it out, and trying to load the real init inside Gentoo root. The progress of each subproject are listed below.

### Writing a "preinit" in C/C++

I've set up [a repository][1] called `preinit_angler`, which currently implements the test function (print haiku into kernel message so that we can verify them on next boot) described in [this article][2]. Implementing the toy init is necessary is because we set up a tiny-platform that we can place other things onto it in this way: maybe password prompts for entering LUKS passphrases, or options to choose different Android snapshots. What's more, this verifies that our toolchain was really generating correctly statically-linked executables that can be directly executed by the kernel. The repository also holds the incomplete code in attempt to implement Android `cryptfs` decryption by hand.

### Attempt to decrypt Android userdata

I've ran into problems tackling the native encryption of Android: after spending a considerable amount of time on reading the code and splitting functions out from `vold`, I ran into the dead end of ARM's Trusted Execution Environment (TEE, learn more about it [here on Wikipedia][3]). The detailed process of my attempt is logged in this article: [Analysis of Android cryptfs][4].

### Bypassing Android force encryption and restructuring userdata partition

As we can't use an encrypted `userdata` for now, and encryption is forced on AOSP for Nexus 6P, we'll need to bypass the policy. The 

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

## Work to be done next week

By the end of next week the first stage of my GSoC 2018 project should have been finished: an Android system successfully booting inside a chroot (and namespaces) under OpenRC init, who gets loaded by `preinit`. Several expected problems/projects exist:

  * The filesystem structure in `userdata` needs working out.
  * If Android `/data` turns into a directory instead of the filesystem root, it will be our responsibility to build Android's mount structure.
  * We'll definitely run into problems, thus a serial console through UART (in headphone jack for Nexus'es and Pixels) is necessary; asynchronous `console-ramoops` does not fulfill the requirement for interactions.
    This requires a headphone-jack UART cable, which was made by @imi415 on Telegram. Thanks a lot!

[1]: https://github.com/KireinaHoro/preinit_angler
[2]: {filename}replace-android-init-with-test-script.md
[3]: https://en.wikipedia.org/wiki/Trusted_execution_environment
[4]: {filename}/Android/analysis-of-android-cryptfs.md
[5]: https://github.com/vincentbernat/jchroot
