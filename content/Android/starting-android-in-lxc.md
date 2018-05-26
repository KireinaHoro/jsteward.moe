Title: Starting Android in LXC
Date: 2018-05-26 13:00
Modified: 2018-05-26 13:00
Category: Android
Tags: android, lxc, gsoc, gentoo
Slug: starting-android-in-lxc
Status: published

## Preface

After successfully booting Gentoo on Nexus 6P [in the previous article]({filename}/Gentoo/booting-gentoo-on-nexus-6p.md), we can move on to launching Android in LXC, which is the last mission in the first period of my GSoC 2018 project.  This article documents the process to bring up Android successfully with most of its functions working; only a few things don't work by now, and they're recorded in the Known Problems section at the end of this article.  Note that while this article strives to provide easy-to-follow instructions, it may not be suitable as a step-by-step tutorial. That is to say, you may encounter problems due to mistakes or things that the author didn't notice.  The author appreciates your understanding when such things happen; meanwhile, feel free to contact the author by the means listed in the page linked at the bottom of this page.

## Legends

Command prompts in this article starts with the hostname of the machine, followed by a `#` or `$`, denoting if the user executing the command need to be root or not.  The following hostnames have special meanings:

  * `yuki`: the Linux workstation
  * `umi`: Gentoo Linux on Nexus 6P
  * `angler`: Android on Nexus 6P

## Set Up Filesystem for Android

Android directly uses the initramfs as its rootfs and mounts other partitions, namely `userdata`, `system`, `cache`, `persist`, and `vendor`, at mountpoints in `/`.  What we need to do here is to copy Android's rootfs to LXC's rootfs location so that we can launch it later on.  Grab a copy of the Android `boot.img` (not the trimmed `preinit` `boot.img`), unpack it with the [Makefile rules in `preinit` repository](https://github.com/KireinaHoro/preinit_angler/blob/61f8fefb1f027eb09dc6ee291f6f990cf032c624/Makefile#L64), tar it up, and transfer the tarball to the phone via adb.  Remember to enable root access for ADB, which can be found in Developer Options in Android.

	yuki $ adb devices
	List of devices attached
	84xxxxxxxxxxxxxx        device
	
	yuki $ adb root
	yuki $ adb shell dd if=/dev/block/bootdevice/by-name/boot | dd of=boot-stock.img
	( ... output elided ... )
	yuki $ mv boot-stock.img ~/preinit_angler/initramfs/boot.img && cd ~/preinit_angler
	yuki $ make unpack
	( ... output elided ... )
	yuki $ cd initramfs/root && tar czvf - . | adb shell "cat >/data/android-root.tar.gz"
	yuki $

Copy the tarball into the Gentoo chroot and enter the chroot.  Create the necessary mountpoints and unpack the root tarball into LXC rootfs.

	yuki $ adb shell
	angler # /data/gnu/start_chroot
	angler # mv /data/android-root.tar.gz /data/gnu/root/
	angler # chroot /data/gnu /bin/su
	umi # mkdir -p /var/lib/android/{system,vendor,data,system,cache}
	umi # mkdir -p /var/lib/lxc/android/rootfs
	umi # tar xvf ~/android-root.tar.gz -C /var/lib/lxc/android/rootfs
	( ... output elided ... )
	umi # mkdir -p /var/lib/lxc/android/run
	umi #
	
We need `/run` in Android rootfs to talk to the host for the `charger` hack later on.
	
Write the following `fstab` entries to `/etc/fstab` in Gentoo, so that OpenRC will take care of mounts on Gentoo startup.

```
# Android mounts
/dev/mmcblk0p43 /var/lib/android/system ext4 ro,barrier=1,inode_readahead_blks=8 0 0
/dev/mmcblk0p32 /var/lib/android/persist ext4 noatime,nosuid,nodev,barrier=1,data=ordered,nomblk_io_submit 0 0
/dev/mmcblk0p37 /var/lib/android/vendor ext4 ro,barrier=1,inode_readahead_blks=8 0 0
/dev/mmcblk0p38 /var/lib/android/cache ext4 noatime,nosuid,nodev,barrier=1,data=ordered,nomblk_io_submit,noauto_da_alloc 0 0
/dev/mmcblk0p44 /var/lib/android/data ext4 noatime,nosuid,nodev,barrier=1,data=ordered,nomblk_io_submit,noauto_da_alloc,inode_readahead_blks=8 0 0

# Bind into container
/var/lib/android/system /var/lib/lxc/android/rootfs/system none bind 0 0
/var/lib/android/persist /var/lib/lxc/android/rootfs/persist none bind 0 0
/var/lib/android/vendor /var/lib/lxc/android/rootfs/vendor none bind 0 0
/var/lib/android/cache /var/lib/lxc/android/rootfs/cache none bind 0 0
/var/lib/android/data /var/lib/lxc/android/rootfs/data none bind 0 0
/run /var/lib/lxc/android/rootfs/run none bind 0 0
```

Boot into Gentoo by temporarily booting the `preinit` `boot.img` to check if the partitions are mounted correctly.  Double-check that the device nodes are correct if things go wrong.  Boot back into Android by rebooting.

## Install LXC in Gentoo Linux

LXC is the core suite to boot Android containerized here.  The installation process is in two parts: installing the userspace utilities, and enabling necessary options in the kernel.

### Userspace Utilities

This is not different from installing normal Gentoo packages.  Enter the chroot and install `app-emulation/lxc`:

	yuki $ adb root
	yuki $ adb shell /data/gnu/start_chroot
	yuki $ adb shell chroot /data/gnu /bin/su
	umi # emerge --verbose --autounmask-write=y app-emulation/lxc
	( ... output elided ... )
	umi # dispatch-conf
	( ... output elided ... )
	umi # emerge --verbose app-emulation/lxc
	( ... output elided ... )
	umi #
	
The process can take a little bit of time to run.  If it's too slow in your case, consider [setting up a cross build environment](https://wiki.gentoo.org/wiki/Cross_build_environment) per instructions on Gentoo Wiki if you have a Gentoo workstation.  That's out of the scope of this article.

### Kernel

According to [LXC on Gentoo Wiki](https://wiki.gentoo.org/wiki/LXC#Kernel_with_the_appropriate_LXC_options_enabled), we need quite many options for LXC's functioning.  I've put how to compile a custom kernel in a separate article: [Building a LXC-ready Android kernel with Gentoo toolchain]({filename}building-lxc-ready-kernel.md).  Follow that article to get a `Image.gz-dtb` file, which is the kernel image that satisfies our needs, and proceed with the following instructions to repack the `preinit` `boot.img`--we no longer need the Android `boot.img` to be `boot` from this point on.

	yuki $ cp Image.gz-dtb ~/preinit_angler/out/zImage && cd ~/preinit_angler
	yuki $ make repack
	( ... output elided ... )
	yuki $
	
The final `preinit` `boot.img` should be located at `out/boot-mod.img`.  Boot the phone into `fastboot`, then _flash_ the new image.

	yuki $ fastboot devices
	84xxxxxxxxxxxxxx        fastboot
	yuki $ fastboot flash boot out/boot-mod.img
	( ... output elided ... )
	yuki $
	
Boot into Gentoo by choosing "Start" in `fastboot`.  Run `lxc-checkconfig` to see if our kernel is suitable.  Not everything's required; as long as you don't see red "missing" on items other than systemd, you're good to go.

```
umi # lxc-checkconfig
--- Namespaces ---
Namespaces: enabled
Utsname namespace: enabled
Ipc namespace: enabled
Pid namespace: enabled
User namespace: enabled
Network namespace: enabled
Multiple /dev/pts instances: enabled

--- Control groups ---
Cgroups: enabled

Cgroup v1 mount points:
/sys/fs/cgroup/openrc
/sys/fs/cgroup/cpuset
/sys/fs/cgroup/debug
/sys/fs/cgroup/cpu
/sys/fs/cgroup/cpuacct
/sys/fs/cgroup/devices
/sys/fs/cgroup/freezer

Cgroup v2 mount points:


Cgroup v1 systemd controller: missing
Cgroup v1 clone_children flag: enabled
Cgroup device: enabled
Cgroup sched: enabled
Cgroup cpu account: enabled
Cgroup memory controller: missing
Cgroup cpuset: enabled

--- Misc ---
Veth pair device: enabled, not loaded
Macvlan: enabled, not loaded
Vlan: missing
Bridges: enabled, not loaded
Advanced netfilter: enabled, not loaded
CONFIG_NF_NAT_IPV4: enabled, not loaded
CONFIG_NF_NAT_IPV6: missing
CONFIG_IP_NF_TARGET_MASQUERADE: enabled, not loaded
CONFIG_IP6_NF_TARGET_MASQUERADE: missing
CONFIG_NETFILTER_XT_TARGET_CHECKSUM: missing
CONFIG_NETFILTER_XT_MATCH_COMMENT: enabled, not loaded
FUSE (for use with lxcfs): enabled, not loaded

--- Checkpoint/Restore ---
checkpoint restore: missing
CONFIG_FHANDLE: enabled
CONFIG_EVENTFD: enabled
CONFIG_EPOLL: enabled
CONFIG_UNIX_DIAG: enabled
CONFIG_INET_DIAG: enabled
CONFIG_PACKET_DIAG: enabled
CONFIG_NETLINK_DIAG: enabled
File capabilities:

Note : Before booting a new kernel, you can check its configuration
usage : CONFIG=/path/to/config /usr/bin/lxc-checkconfig

umi #
```

## Bring Android up in LXC container

Now that we have LXC correctly configured, we can set up the Android container.  Some modifications to Andoid's `fstab.<device>` and `init.rc` are needed for a successful boot.  Some hacks are required to fix some functions, of which we'll discuss in the next section.  Commands in this section are expected to be executed with Gentoo booted up with `preinit`, not in the chroot from Android.


The modified files' patches as well as helper scripts are put together in [a repository on GitHub](https://github.com/KireinaHoro/android-lxc-files).  Make sure that you apply them before continuing.

Place `pre-start.sh`, `post-stop.sh`, and `config` in `/var/lib/lxc/android`.  Make sure that the executable bit is there for the scripts.  Issue the following to see if LXC has recognized the container:

	umi # lxc-info android
	Name:           android
	State:          STOPPED
	
If everything's going as expected, start the container, and we'll see Android booting up on the device screen.

	umi # lxc-start android
	umi #
	
If the container failed to start, issue the following and then examine `start.log` to see what's wrong:

	umi # lxc-start -l debug -o start.log -n android
	( ... error output elided ... )
	umi #
	
Verify that things are working, especially the hardware.  In case something's crashing, or the Android framework failed to start at all, connect the phone to the computer via USB and check out `logcat` via ADB (it starts pretty early).  Tombstones at `/data/tombstones` in Android root are usually helpful; consult [this article](https://source.android.com/devices/tech/debug/) for how to read them.

	yuki # adb logcat | less
	yuki # adb shell
	angler # cd /data/tombstones

Only some small bits don't work by now, and we'll cover them in the following section.

## Improvements

### Container Auto-start

It's tiresome to attach a serial cable and issue `lxc-start android` to boot Android every time.  Create `lxc.android` service and add it to the `boot` runlevel, as Android takes care of most of the device-specific work, namely networking:

	umi # cd /etc/init.d
	umi # ln -s lxc lxc.android
	umi # rc-update add lxc.android boot
	
### Dial Home from Android world

Having to attach serial cable to access Gentoo is just too tiresome.  Configure `ssh` so that the Android guest can `dialhome`.

	angler # ssh-keygen -t ed25519 -C android -f /data/ssh/id_ed25519

Enable `sshd` in Gentoo, configure `authorized_keys` for root, and put a little script `dialhome` (available in [`scripts/` in the `android-lxc-files` repository](https://github.com/KireinaHoro/android-lxc-files/tree/master/scripts)) for quick access:

	umi # umask 077
	umi # mkdir -p ~/.ssh
	umi # cat /var/lib/android/data/ssh/id_ed25519.pub >> ~/.ssh/authorized_keys
	umi # cp dialhome /var/lib/android/data/ssh/
	umi # chmod u+x /var/lib/android/data/ssh/dialhome
	umi # chown 2000:2000 /var/lib/android/data/ssh/dialhome
	umi # rc-update add sshd default
	
We can now issue `/data/ssh/dialhome` to log into Gentoo.  No more serial cable needed unless something goes wrong.  We can safely disable ADB root access from Android Developer Settings by now.

Note that you can `lxc-attach android` from Gentoo world!  This will launch `/bin/sh`, which is the busybox sh.  You may need to set `PATH` to include `/system/bin` to get Android's utilities.

### Fix Charger Mode

Android's init knows whether it's plugged into the charger while powered off.  If that's the case, it launches `/sbin/charger`, which draws the charging animation on the screen.  Long-pressing the power button causes a restart, and the system will boot into normal Android.  Unfortunately, our LXC stop hooks can't tell if the container ended with a poweroff or a restart, thus we won't be able to exit charger mode unless we unplug the power source.

The solution is quite simple: replace `/sbin/charger` with a simple script that places a marker file in `/run` (which is also GNU/Linux's `/run`), and then call the real charger, which is now `/sbin/charger.real`.  The `post-stop.sh` hook can then reboot if it sees that marker file.  The script is available [here](https://github.com/KireinaHoro/android-lxc-files/blob/master/scripts/charger).

## How It Worked

If you take a look at the config for LXC, the start-stop hooks, and the `init.rc` patch, you'll discover that we needed to correct paths for cgroup pseudo-filesystems and set `rt_runtime_us` RT schedule parameters.  Android uses cgroups heavily as well, and we need to get it correct so that Android doesn't end up writing to the host's cgroup space.  We need to set `rt_runtime_us` to allocate realtime bandwidth to the cgroup, otherwise realtime schedulers will fail.  The following should be helpful to grab a general understanding of group scheduling:

  * [Real-Time group scheduling](https://www.kernel.org/doc/Documentation/scheduler/sched-rt-group.txt)
  * [How do I configure LXC to allow the use of SCHED_RR in a container?](https://serverfault.com/questions/630220/how-do-i-configure-lxc-to-allow-the-use-of-sched-rr-in-a-container/632564)

The rest of things (filesystem mounting, etc.) are pretty straightforward.  Note that we need to tell Android (`vold` to be specific) not to touch mounting, by commenting out `fstab` entries for the relevant partitions.  Due to [poorly-written `vold` code without `nullptr` checks](https://android.googlesource.com/platform/system/vold/+/master/cryptfs.cpp#2919), we need an empty entry in Android `fstab`, otherwise `vold` will crash.

We bind `/run` from GNU/Linux Android so that the container can talk to the host, informing the host about its states (such as "We're in charger mode: reboot when I finish instead of power off").  `/run` was chosen because it's the place to hold runtime files by convention on a GNU/Linux system.  Read [this article](http://www.h-online.com/open/news/item/Linux-distributions-to-include-run-directory-1219006.html) for more information.

## Known Problems

The (non-exhaustive) list of problems as of 2018-05-26:

  * Reboot function in Android system (along with Advanced Reboot) doesn't work.  This is because Android system doesn't actually poweroff the system or reboot it when inside a container: it simply performs `exit(0)`, making it impossible for the GNU/Linux world (at least for now) to tell how the container stopped.  The current behavior is that the system will power down regardless of whether "Poweroff" or "Reboot" (or other reboot options, e.g. Reboot to bootloader) has been selected in Android.
    * `charger` suffers from similar problems, though a workaround works pretty well; see The Charger section above.
	* This may be fixed by patching Android framework so that it signals the host about how it ended, by placing a file in the `/run` filesystem bind-mounted from the host.  The host then decides whether to reboot or to poweroff according to the signal file.  This is exactly how `charger`'s problem gets fixed.
  * Boot is unbearably slow.  Charging while powered off takes a long time to show the charging animation as well.
    * This is because the _Linux kernel's initialization time_ is long.  It takes over 10 seconds for the kernel to launch the first userspace program--`preinit`.
	* For better experience, the kernel should have most of its functions as kernel modules, so that we can display a boot animation (or a static picture other than the Google logo from bootloader) as early as possible.  We may draw an animation that's unrelated to `bootanim` in Android though.
  * Full-disk encryption / file-based encryption doesn't work.
	* This was done deliberately, as Android's `cryptfs` implementation is a little bit too complicated to implement (see [my previous analysis on Android cryptfs]({filename}analysis-of-android-cryptfs.md)).
	* Standard encryption means should get implemented at some point (e.g. LUKS).
	* Choosing to encrypt device in System Settings in Android can cause __unexpected behaviors__.  _YOU HAVE BEEN WARNED._
