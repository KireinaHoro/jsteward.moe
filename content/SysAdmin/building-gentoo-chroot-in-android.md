Title: Building a Gentoo chroot in Android
Date: 2018-05-04 11:00
Modified: 2018-05-05 23:00
Category: SysAdmin
Tags: android, gentoo, gsoc
Slug: building-gentoo-chroot-in-android
Status: published

## Preface

Chrooting is usually a key part in installing a GNU/Linux system, and there's no difference here in my GSoC 2018 work. In this article we'll build a Gentoo chroot with `CHOST=aarch64-unknown-linux-gnu`, set up ssh connection to it, and install some necessary tools.

## Preparation work

First of all, we need to find somewhere to store our chroot. Connect the phone to the computer, authorize adb access on the phone, then issue the following:

	$ adb root   # remember to enable root access for adb in Developer Options
	restarting adbd as root
	$ adb shell
	angler:/ # mkdir -p /data/gentoo && cd /data/gentoo
	angler:/data/gentoo #

Then, we need to fetch the `stage3` image corresponding to the architecture--`aarch64` for Nexus 6P. Currently, `aarch64` stages are not stable yet. The current status of Gentoo's ARM64 Project can be found [here][1]. According to the developers on [gentoo-dev](mailto:gentoo-dev@lists.gentoo.org) in [this email](https://archives.gentoo.org/gentoo-dev/message/9f25d996bcc00e318bdfa2ec4e071be4), despite the fact that arm64 is still experimental for Gentoo, development is definitely taking place and we're getting packages keyworded every day. Consequently, arm64 seems to be a better choice than arm.

As no arm64 profiles are stable as of writing, I'll use the experimental stages, and they're located in `experimental/arm64` in the Gentoo mirror you choose. The link I used is [here][2]. You can either download the tarball on your device directly, or transfer it to the phone via `adb push` after downloading it on your computer. Move the tarball to `/data/gentoo/` for the next step.

## Unpack tarball, mount filesystems, and chroot

Unpack the tarball:

	angler:/ # cd /data/gentoo
	angler:/data/gentoo # tar xvf stage3-*.tar.bz2
	( ... lines of output elided ... )
	angler:/data/gentoo # ls
	bin boot dev etc home lib lib64 media mnt opt proc root run sbin sys tmp usr var
	angler:/data/gentoo #

Clean up the bogus device nodes in stage3 tarball, and mount the necessary psuedo-filesystems:

	angler:/data/gentoo # rm -rf dev/* tmp/*
	angler:/data/gentoo # for a in proc sys dev; do mount --rbind {/,}$a && mount --make-rslave $a; done
	angler:/data/gentoo # mkdir -p dev/shm
	angler:/data/gentoo # chmod 777 dev/shm
	angler:/data/gentoo # mount -t tmpfs tmpfs dev/shm
	angler:/data/gentoo # mount -t devpts -o gid=5 devpts dev/pts # requirement of portage's configure
	angler:/data/gentoo # mount -t tmpfs tmpfs tmp

Change root into `/data/gentoo`, set up timezone, `resolv.conf`, ssh public keys, and edit `make.conf` so we have an environment that works properly.

	angler:/data/gentoo # chroot . /bin/su
	localhost / # echo "nameserver 101.6.6.6" >> /etc/resolv.conf
	localhost / # echo "Asia/Shanghai" > /etc/timezone
	localhost / # emerge-webrsync
	( ... lines of output elided ... )
	localhost / # emerge --config timezone-data
	( ... lines of output elided ... )
	localhost / # emerge -v mosh --autounmask-write
	( ... lines of output elided ... )
	localhost / # ssh-keygen -A
	ssh-keygen: generating new host keys: RSA DSA ECDSA ED25519

We can now connect to the chroot environment via `mosh`. For ease of starting the environment, we create the following script `/data/gentoo/start_chroot`:

```bash
#!/system/bin/sh

mount --rbind /proc /data/gentoo/proc
mount --make-rslave /data/gentoo/proc
mount --rbind /sys /data/gentoo/sys
mount --make-rslave /data/gentoo/sys
mount --rbind /dev /data/gentoo/dev
mount --make-rslave /data/gentoo/dev
mkdir -p /data/gentoo/dev/shm
chmod 777 /data/gentoo/dev/shm
mount -t tmpfs tmpfs /data/gentoo/dev/shm
mount -t devpts -o gid=5 devpts /data/gentoo/dev/pts
mount -t tmpfs tmpfs /data/gentoo/tmp

exec chroot /data/gentoo /usr/sbin/sshd
```

After the system reboots, we can issue the following to bring up the sshd inside the chroot:

	$ adb root
	restarting adbd as root
	$ adb shell /data/gentoo/start_chroot
	$

And, as a bonus, we can restart `adbd` on the phone to kill all process spawned by it, including the entire chroot:

	$ adb unroot


[1]: https://wiki.gentoo.org/wiki/Project:ARM64
[2]: https://mirrors.tuna.tsinghua.edu.cn/gentoo/experimental/arm64/stage3-arm64-20180305.tar.bz2
