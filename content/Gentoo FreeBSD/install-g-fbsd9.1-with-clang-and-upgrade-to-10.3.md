Title: Install Gentoo/FreeBSD 9.1 with Clang and Update to 10.3
Date: 2017-09-01 0:00
Modified: 2017-09-01 0:00
Category: Gentoo FreeBSD
Tags: system, gentoo, freebsd, clang
Slug: gfbsd-clang-9.1-to-10.3

## Preface

As a result of simple stupidity of deleting the wrong virtual machine snapshot
thus losing the already-configured G-FBSD Clang environment, I have to start
over again. This article is for future reference and (probably?) save the 
future headaches and nightmares.

## Install 9.1

We need to install Gentoo FreeBSD 9.1 first in order to upgrade it to 10.3
later.

### Setting up the installation environment

Grab any FreeBSD installation media. A bootonly image will be fine as we'll
only be using the Live CD feature.

    dd if=FreeBSD-11.1-RELEASE-amd64-bootonly.iso of=/dev/sda status=progress

Make sure that you get the `/dev/sda` device node correct as a small typo may
trash your current system.

Boot the installation media and select **Live CD**. For ease of operating (as
well as the ability to scroll up the buffer to see what has happened with the
help of tmux) using ssh to connect to the target machine is recommended. Mount
a `unionfs` at the Live CD's `/etc` so that we can enable root login for `sshd`
(for the sake of convenience). Do not do this on a production server!

    mkdir /tmp/etc
    mount -t tmpfs tmpfs /tmp/etc
    mount -t unionfs /tmp/etc /etc
    echo "PermitRootLogin yes" >> /etc/ssh/sshd_config
    passwd

Now set up the network and bring up `sshd`.

    dhclient em0
    /etc/rc.d/sshd onestart

We are now ready to connect to the target machine to deploy the system. Use
ssh client to connect and then proceed to the next section.

### Setting up the disks

Things are rather straightforward for a virtual machine. If your setup is on a
real machine, adjust the following commands accordingly and refer to `gpart(8)`
when needed. We'll be using UFS as the root filesystem. If you want to use ZFS
refer to the relevant sections [here in the old Gentoo FreeBSD installation
guide][old-guide].

    gpart create -s GPT ada0
    gpart add -s 64k -t freebsd-boot ada0
    gpart add -s 38G -t freebsd-ufs -l root ada0
    gpart add -t freebsd-swap -l swap ada0

Create and mount the filesystems.

    newfs -U /dev/gpt/root -L gfbsdroot
    mount /dev/ufs/gfbsdroot /mnt
    swapon /dev/gpt/swap

### Unpacking the `stage3` tarball and chrooting

Fetch and unpack the stage3 tarball. The current tarball is based on FreeBSD
9.1. After I create the new tarballs based on 10.3 those can be used to install
the system. Change the mirror site accordingly if you do not use TUNA's. Any
mirror site with the complete Gentoo reposiroty will have these stages.

    cd /mnt
    fetch https://mirrors.tuna.tsinghua.edu.cn/gentoo/experimental/bsd/freebsd/stages/amd64-fbsd-9.1/clang/stage3-amd64-clangfbsd-9.1.tar.bz2
    fetch https://mirrors.tuna.tsinghua.edu.cn/gentoo/snapshots/portage-latest.tar.bz2

Unpack the tarball.

    setenv LANG "en_US.UTF-8"
    tar xjpf stage3*.tar.bz2 -C /mnt
    tar xjf portage-latest.tar.bz2 -C /mnt/usr

Prepare the installation root and chroot into it. If you don't have enough RAM,
do not mount a `tmpfs` at `/var/tmp`.

    mount -t devfs devfs /mnt/dev
    mount -t fdescfs fdesc /mnt/dev/fd
    mount -t tmpfs tmpfs /var/tmp
    cp /etc/resolv.conf /mnt/etc
    chroot /mnt /bin/bash

### Configuring the system

Set the timezone and update portage. As the current tree has proceeded into
`EAPI=6`, we'll need to update Portage in a rather inelegant way. Never use the
`--nodeps` option with Portage unless you're told to do so and you exactly know
what you're doing!

    env-update && source /etc/profile
    cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime
    PYTHON_TARGETS="python2_7" emerge -a1 dev-lang/python-exec
    PYTHON_TARGETS="python2_7" emerge -a1 sys-apps/portage
    
We need to temporarily disable `dev-libs/ncurses[cxx]` as it will cause
problems with the current toolchain.

    mkdir -p /etc/portage/package.use
    echo "sys-libs/ncurses -cxx" > /etc/portage/package.use/ncurses
    emerge -a1 portage libtool eselect openrc
    emerge -ac python
    sed -i -e 's/python3.3//' /etc/python-exec/python-exec.conf
    eselect python set python3.4

Note that we have also upgraded `python` in the process, as the 9.1 stage is
shipped with Python 2.7, 3.2 and 3.3, above which Portage won't properly work.

Pick an editor of your choice. Don't worry if you're presented with missing
keywords. A missing keyword just means that the package has not been tested
with the platform, not that it will not work. You can file a bug report to add
a keyword for that package if it *does* work. :)

    emerge -av app-editors/vim
    eselect editor set vi

Edit `make.conf` accordingly. You may add `GENTOO_MIRRORS` or tailor `MAKEOPTS`
so that the compiling that's following fully utilizes the system's potential.
Remove the obsolete `mmx sse sse2` USE flags.

    vim /etc/portage/make.conf

Set up `repos.conf` to sync properly. You don't need to perform a sync now, as
the snapshot is almost up-to-date thus suitable.

    mkdir -p /etc/portage/repos.conf
    cp /usr/share/portage/config/repos.conf /etc/portage/repos.conf/gentoo.conf

Install the kernel source and compile a kernel.

    USE=symlink emerge -a freebsd-sources
    emerge -au1 sys-devel/flex
    cd /usr/src/sys/amd64/conf
    cp GENERIC.hints /boot/device.hints
    config GENERIC
    cd ../compile/GENERIC
    make cleandepend && make depend && make -j4 && make install

Edit the fstab accordingly, set the hostname, network options, local password,
local keymap, and add a normal user.  For more detailed information, refer to
the [Gentoo Handbook][handbook].

Here's a sample fstab:

    /dev/ufs/gfbsdroot /       ufs     rw 0 0
    /dev/gpt/swap      none    swap    sw 0 0
    fdesc              /dev/fd fdescfs rw 0 0

Note that the `fdescfs` is needed as `bash` requires that to work properly.

    vim /etc/fstab
    vim /etc/conf.d/hostname
    vim /etc/conf.d/net
    cd /etc/init.d
    ln -s net.lo0 net.em0
    rc-update add net.em0 default
    passwd
    adduser
    emerge -av app-admin/sudo
    visudo

Set up `sshd` if you wish to connect remotely.

    emerge -au1 net-misc/openssh
    rc-update add sshd default

Install a DHCP client.

    emerge -a net-misc/dhcpcd

Install the bootloader. If you followed the earlier steps to partition the
disk, the only choice is FreeBSD's `boot0`.

    emerge -a sys-freebsd/boot0
    gpart bootcode -b /boot/pmdr ada0
    gpart bootcode -p /boot/gptboot -i 1 ada0

The installation is now complete. Reboot the system to test it out.

## Upgrade the system to 10.3

Basically we the following steps:

  - Bootstrap a newer version of the LLVM Clang toolchain
  - Upgrade the kernel then reboot (the new userland may use functions that are
only available in the newer kernel)
  - Upgrade the FreeBSD userland
  - Change the `CHOST` variable then rebuild the toolchain
  - Rebuild (thus upgrading in the process) everything (`@world`)
  - Clean up, rebuild packages that need the old libraries (`@revdep-rebuild`)

Note that some of the packages need patching in order to work correctly. The
bug ID at Gentoo Bugzilla will be provided when introducing a patch. Feel free
to revert them provided that the corresponding bugs got fixed.

### Preparation work

Select the correct profile. Note that we're going to use Clang as the system
compiler so make sure that you've chosen a `clang` profile.

    eselect profile list
    eselect profile set default/bsd/fbsd/amd64/10.3/clang

Upgrade Portage. If `EAPI` masks occur, you need to update portage with [a
manual method][manual-update-portage].

    emerge -avu1 sys-apps/portage

Upgrade some packages to proceed with the upgrading work. Note that
`>=app-arch/libarchive-3.3` requires new macros in the system headers, thus
can't be built for now. We'll need to mask it temporarily.

    echo ">=app-arch/libarchive-3.3" >> /etc/portage/package.mask
    emerge -a1 --nodeps sys-freebsd/freebsd-mk-defs
    emerge -au1 sys-apps/findutils --exclude sys-freebsd/*
    emerge -a1 sys-devel/libtool --exclude sys-freebsd/*
    emerge -au1 sys-devel/flex sys-devel/patch sys-devel/m4 net-libs/libpcap sys-devel/gettext app-arch/libarchive dev-util/dialog --exclude sys-freebsd/*
    emerge -a1 sys-devel/libtool --exclude sys-freebsd/*

[WIP]

[old-guide]: https://wiki.gentoo.org/wiki/Gentoo_FreeBSD#Using_the_ZFS_file_system_.28experimental.29_.2F_.28GPT.29

[handbook]: https://wiki.gentoo.org/wiki/Handbook:AMD64/Installation/System

[manual-update-portage]: https://wiki.gentoo.org/wiki/Gentoo_FreeBSD/Upgrade_Guide#Update_the_portage_with_a_manual_method.
