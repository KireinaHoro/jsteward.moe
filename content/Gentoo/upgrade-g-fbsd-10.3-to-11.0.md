Title: Upgrade Gentoo FreeBSD 10.3 to 11.0
Date: 2017-09-07 0:00
Modified: 2017-09-07 0:00
Category: Gentoo
Tags: system, gentoo, freebsd
Slug: gfbsd-10.3-to-11.0
Status: published

## Preface

Now that we have successfully upgraded Gentoo FreeBSD from 9.1 to 10.3, we
need to upgrade it to 11.0 in order to catch up the latest FreeBSD system.
The major steps consist of the following:

 - Upgrading world
 - Changing to the new profile
 - Upgrade the kernel
 - Upgrade the userland
 - Change `CHOST` and rebuild the toolchain

Let's start.

## World upgrade

Remember to sync the repositories beforehand to make sure we're on the most
recent version of the Portage tree.

    emerge --sync
    emerge -avuDN @world

## Switch to the latest profile

    eselect profile list
    eselect profile set default/bsd/fbsd/amd64/11.0

## Upgrade the kernel

It's important to upgrade the kernel first as some userland utilities may
require the newer functions in the kernel.

    emerge -a1 --nodeps sys-freebsd/freebsd-mk-defs
    emerge -a1 --nodeps sys-freebsd/freebsd-sources
    reboot

Check the running kernel by `uname`:

    uname -a

## Upgrade the FreeBSD userland

Check and remove strange flags from `CFLAGS`. The most basic configuration
should consist of simply `CFLAGS="-O2 -pipe"`.

    vim /etc/portage/make.conf

Seems like GCC 6 doesn't play well when building `freebsd-lib`
([here if you're interested][stackoverflow-post]), and we'll need
`sys-devel/gcc:5.4.0` for now.

    emerge -av sys-devel/gcc:5.4.0
    gcc-config -l
    gcc-config 1

Upgrade the core libraries first.

    emerge -a1 --nodeps sys-freebsd/freebsd-share sys-freebsd/freebsd-lib sys-freebsd/freebsd-libexec

Upgrade the rest of the userland.

    emerge -a1uN boot0 freebsd-bin freebsd-lib freebsd-libexec freebsd-mk-defs freebsd-pam-modules freebsd-sbin freebsd-share freebsd-ubin freebsd-usbin

Re-merge all these packages once again as some of them require header files
from 11.0, which aren't available before.

    emerge -a1 boot0 freebsd-bin freebsd-lib freebsd-libexec freebsd-mk-defs freebsd-pam-modules freebsd-sbin freebsd-share freebsd-ubin freebsd-usbin

## Change the `CHOST` variable and rebuild the toolchain

Edit `/etc/portage/make.conf` and change the `CHOST` variable from 10.3 to
11.0.

    vim /etc/portage/make.conf
    emerge -av1 binutils gcc

Make sure you use the correct version of `binutils` and `gcc`:

    gcc-config -c
    binutils-config -c

Rebuild world with the new toolchain:

    emerge -a1 sys-devel/libtool
    emerge -ae @world --exclude sys-apps/portage
    emerge -a1 sys-apps/portage

If any of the packages fail to build you can resume the build, skipping
that package with:

    emerge -ar --skipfirst

## Clean up

Rebuild packages with preserved libraries:

    emerge @preserved-rebuild
    dispatch-conf

[stackoverflow-post]: https://stackoverflow.com/questions/46129786/isystem-generated-by-make-disturbing-header-search-order-with-gcc-6
