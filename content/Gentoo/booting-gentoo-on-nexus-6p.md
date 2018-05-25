Title: Booting Gentoo on Nexus 6P
Date: 2018-05-25 20:00
Modified: 2018-05-25 20:00
Category: Gentoo
Tags: android, gentoo, gsoc
Slug: booting-gentoo-on-nexus-6p
Status: published

## Preface

As we now have `preinit` and the crucial UART console available, we can start bringing up the real GNU/Linux system--Gentoo Linux in this case.  This article will focus on the following topics:

  * Filesystem structure and mounting procedure (in details)
  * Launch sequence to bring up OpenRC
  * Crafting a `preinit` initramfs
  * Tweaks in Gentoo to get ready to start Android in LXC later on
  
## Filesystem Structure and Mounting Procedure

We won't be changing the partition table, as altering that will prevent `fastboot flash` commands from working properly, and we won't be able to recover unless we re-flash the EMMC chip if we messed the partition table up.  The partition we'll use for GNU/Linux root is `userdata`, but not the entire filesystem--we can retain compatibility with stock Android `boot.img` by preserving `userdata` as the partition to be mounted for Android `/data`.  The Gentoo root filesystem sits at `userdata:/gnu`, and gets binded to `/` in `preinit`.

After OpenRC boots, `userdata`, `system`, `vendor`, `persist`, and `cache` gets mounted to their mountpoints under `/var/lib/android` for launching Android later on.  This is done by the `localmount` service in OpenRC's `sysinit` runlevel, by reading `/etc/fstab` in Gentoo root.  These partitions later get bind-mounted into Android's LXC rootfs, which will be the topic for my next article.
  
## Launch Sequence to Bring up OpenRC

Once kernel finishes its early initializations, `preinit`, a busybox sh script, gets called.  The source is available [here in the `preinit` repository](https://github.com/KireinaHoro/preinit_angler/blob/141cccc95e0f925e2e1be3cfd02d1e12eabef577/src/init).  Preinit basically does the following:

  * Mount pseudo-filesystems for `preinit`'s proper functioning
  * Mount `userdata` partition at `/mnt/userdata`
  * Bind-mount `/mnt/userdata/gnu` to itself, making it a mountpoint, which was mandatory for `switch_root`
  * `exec switch_root` into `/mnt/userdata/gnu` and call `/sbin/init` 
  
This procedure does not differ much from standard `initramfs`es, except that the desired root is not the filesystem root.  We can add other things into `preinit` later on to support alternative root layouts, e.g. LUKS.

## Crafting a Preinit initramfs

As we're not launching anything other than `/init`, and, unlike Android, we have a real root filesystem instead of the entire root on `tmpfs`, we can safely trim unnecessary components inside the initramfs.  What we really need in the initramfs is as follows:

  * `init`: busybox sh script (duh)
  * `busybox`: static executable
  * symlinks to `busybox` applets under `/bin`
  * mountpoints
  
The complete `initramfs` layout can be found in [the `preinit` repository](https://github.com/KireinaHoro/preinit_angler/tree/141cccc95e0f925e2e1be3cfd02d1e12eabef577/initramfs/root).  Repack `boot.img` with the Makefile rules at the root of `preinit` repository.  Remember to turn SELinux to `permissive` in kernel commandline: though OpenRC won't respect that commandline option, Android init will load the policies and enforce it later on, and as we're not SELinux-ready now, that would certainly break things.

Boot the phone into `fastboot` mode, but don't hurry to flash that `boot.img` as the `boot` partition yet--use the following commandline to boot the new `boot.img` temporarily, so that we still have the regular Android `boot.img` for debug and further actions that require a working Internet connection:

	fastboot boot <modded boot.img>

Attach the UART cable to see what's going on.  If the kernel can't launch init, double-check that the `init` script is executable, and the shebang line is correct.  Also check if the symlinks to `busybox` are placed correctly.  If everything goes as expected, you should see our dear Preinit and OpenRC waving hello to you:

	[   12.602544] new_era: Preinit started
	mount: /etc/mtab: No such file or directory
	mount: /etc/mtab:[   12.606728] new_era: Trying to mount /dev/mmcblk0p44 on /mnt/userdata...
	 No such file or directory
	[   12.735390] EXT4-fs (mmcblk0p44): mounted filesystem with ordered data mode. Opts: (null)
	mount: /etc/mtab: No such file or directory
	[   12.743008] new_era: Setting up /mnt/userdata/gnu as mountpoint...
	mount: /etc/mtab: No such file or directory
	[   12.767932] new_era: Cleaning up mounts, switching root to /mnt/userdata/gnu, and launching /sbin/init...
	mount: /etc/mtab: No such file or directory
	mount: /etc/mtab: No such file or directory
	mount: /etc/mtab: No such file or directory
	INIT: version 2.88 booting

	   OpenRC 0.34.11 is starting up Gentoo Linux (aarch64)

	 * /proc is already mounted
	 * Mounting /run ...
	 * /run/openrc: creating directory
	 * /run/lock: creating directory
	 * /run/lock: correcting owner
	 * Caching service dependencies ...


## Tweaks in Gentoo to get ready to start Android in LXC later on

Though the system is up and running, we need to tweak a few things to make it suit our later launching Android in LXC.  In case a shell is not yet available on serial console (which is most likely the case by default), boot into Android and `chroot` into Gentoo root as described in [this article](https://jsteward.moe/building-gentoo-chroot-in-android.html) to configure the following.

You'll notice that we don't have a `getty` on the serial console: `sysvinit` does not start `getty` on `ttyHSL0` by default.  Edit `/etc/inittab` in Gentoo root, comment out `tty*` lines (which Android devices definitely don't have) and add the following line:

	s0:12345:respawn:/sbin/agetty -L 115200 ttyHSL0 vt100

Remove `udev` from `sysinit` runlevel.  It inteferes with Android's `ueventd`, and sometimes it takes ages for `udev` to process the `uevents` from the kernel.  `keymaps` and `termencoding` are useless as well, as we'll only use a serial console, on which these services don't make sense.

	for a in {udev,keymaps,termencoding}; do rc-update del $a boot; done
	
Though we do not have networking by now, add `sshd` to the `default` runlevel.  Add `syslog-ng` as well.

	for a in {sshd,syslog-ng}; do rc-update add $a default; done
	
Reboot.  The system should now be running properly.  In the next article, we'll boot back into Android to install LXC in Gentoo root, and we'll then launch Android in LXC.

