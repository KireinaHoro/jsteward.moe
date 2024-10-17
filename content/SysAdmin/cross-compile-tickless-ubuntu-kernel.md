Title: Cross-compiling a Tickless Ubuntu Kernel
Date: 2024-10-16T11:55+02:00
Modified: 2024-10-16T11:55+02:00
Category: SysAdmin
Tags: ubuntu, linux, kernel
Slug: cross-compile-tickless-ubuntu-kernel

## Preface

trial-and-error, not working yet.  Get familiar with the Debian/Ubuntu packaging infrastructure, for future custom packages for debian

[TOC]

## Motivation

Tickless setup: CONFIG_NO_HZ_FULL, HZ=100 for focal.  Used for arm64 Enzian for experiments

Possible to use upstream tree directly, as of [Enzian wiki][5], but feels dirty:
- divergence from stock ubuntu kernel -- no vendor patches
- unhygenic installation of modules, untracked by dpkg

[Official instruction][1] or with `dpkg-buildpackage` works to build on the Enzian, but disk space limit and old CPU -> slow

Conclusion: try to cross compile

## Create variant and build natively on Enzian

Start with focal tree.  Set up fork as [git-scm][6]: shallow clone and allow replace history.  Allow tracking upstream changes back

choice: Set-up Variant vs extra version number (suggested by @shankerwangmiao)

Variant setup: [all changes][7]
- add variant in control.d vars
- declare flavour in `arm64.mk`
- `fakeroot debian/rules clean` to generate
- `fakeroot debian/rules editconfigs` to change annotations
- add changelog item `DEBEMAIL='Pengcheng Xu <email>' dch -c debian.master/changelog -l+pengxu`

## Cross compile

Nothing succeeded -> bad attempts vs proper (but still failed) attempt

### Bad attempt: invoking the rule directly

not clear how to reliably cross compile (`arch=arm64` is not enough--
  kernel compiles but `dpkg` packaging fails) -- attach failure log again

### Bad attempt: `dpkg-buildpackage` with custom targets

- attempt the same thing for building directly on Enzian
- command: `dpkg-buildpackage -uc -us -d -a arm64 -T 'binary-headers,binary-tickless,binary-perarch' --as-root`
- missing targets -> missing packages (e.g. linux-tools, etc.) -> uninstallable; happens when building the newest version in the repo that is not yet pushed

### Proper attempt: set up [sbuild][2] and chroot

suggested by @harry_chen.

- rootless to use build infra in the group -> mmdebstrap instead of schroot
    - setup for the blades (to Roman)
        - dependencies: lz4 sbuild mmdebstrap, uidmap
        - setup `/etc/subgid` for rootless (with mmdebstrap workaround below)
    - `mmdebstrap --arch="amd64 arm64" focal ~/.cache/sbuild/focal-amd64.tar.lz4 ~/0000sources.list`
        - do not use the `buildd` profile since `apt-get` is missing there
    - ubuntu 22.04 mmdebstrap checks for groupname instead of username in `/etc/subgid`
        - ETH LDAP have different user and group name (`pengxu` vs `pengxu-group`)
        - fixed by [upstream][3] but not included in 22.04 (0.8.4-1ubuntu0.1)
        - temporary fix by duplicating name
        - ubuntu &lt;bug url&gt;
    - issues with ports archive -> custom sources.list
    - `sbuild-update --chroot-mode=unshare -udcar` to update the chroot
        - `sbuild` on Ubuntu 22.04 doesn't recognise tar.zst-compressed tarballs, despite the [Debian wiki][2] recommending it
        - Using lz4 since it's the fastest according to [this benchmark][4]

```text
deb [arch=amd64] http://archive.ubuntu.com/ubuntu/ focal main restricted universe multiverse
deb [arch=amd64] http://archive.ubuntu.com/ubuntu/ focal-updates main restricted universe multiverse
deb [arch=amd64] http://archive.ubuntu.com/ubuntu/ focal-backports main restricted universe multiverse
deb [arch=amd64] http://security.ubuntu.com/ubuntu/ focal-security main restricted universe multiverse

deb [arch=arm64] http://ports.ubuntu.com/ubuntu-ports/ focal main restricted universe multiverse
deb [arch=arm64] http://ports.ubuntu.com/ubuntu-ports/ focal-updates main restricted universe multiverse
deb [arch=arm64] http://ports.ubuntu.com/ubuntu-ports/ focal-backports main restricted universe multiverse
deb [arch=arm64] http://ports.ubuntu.com/ubuntu-ports/ focal-security main restricted universe multiverse
```

ubuntu kernel still doesn't cross compile: mix-up between build and host dependencies (`libssl-dev` is main offender but other ones like `pahole` also fails but does not abort build)

- Asked on #kernel:ubuntu.com (Matrix), Timo Aaltonen (@tjaalton:ubuntu.com) confirmed that this is not ideal and I should file a bug
    - he used a foreign schroot and therefore it's emulated "native" build
    - &lt;bug url&gt;

## Closing remarks

Keep an eye on the bugs, once they get fixed we can do this!

[1]: https://wiki.ubuntu.com/Kernel/BuildYourOwnKernel
[2]: https://wiki.debian.org/sbuild
[3]: https://gitlab.mister-muffin.de/josch/mmdebstrap/commit/374ae3dc99e5d8a5a176939c3846e790e890a0e7
[4]: https://linuxaria.com/article/linux-compressors-comparison-on-centos-6-5-x86-64-lzo-vs-lz4-vs-gzip-vs-bzip2-vs-lzma
[5]: https://unlimited.ethz.ch/x/36omD
[6]: https://git-scm.com/book/en/v2/Git-Tools-Replace
[7]: https://github.com/KireinaHoro/linux-focal-variants/compare/8adb6ccd..5.4-tickless?diff=unified&w=
