Title: Cross-compiling a Tickless Ubuntu Kernel
Date: 2024-10-16T11:55+02:00
Modified: 2024-10-16T11:55+02:00
Category: SysAdmin
Tags: ubuntu, linux, kernel
Slug: cross-compile-tickless-ubuntu-kernel

## Preface

This article documents the trial-and-error process of me trying to
cross-compile the Ubuntu kernel for `arm64`, for use with [Enzians][8] at the
[Systems Group at ETH][9].  So far building natively on the Enzians work (see
[native build below](#create-variant-and-build-natively-on-enzian)), but
unfortunately none of the cross-compile approaches works.  I have submitted a
couple bug reports and will (hopefully) update accordingly when things change.

With that said, this whole process has been quite a journey: I learned a lot
about the Debian and Ubuntu packaging infrastructure.  This should serve as a
good starting point for later, when I would want to create my own, custom
Debian packages.

[TOC]

## Motivation

### Why custom kernel?

The core idea is very simple: when doing performance measurements for a
user-space application, one would want as little disruption as possible.  This
is traditionally handled by _pinning_ a task to a specific CPU core, to avoid
the scheduler moving it willy-nilly across cores.  Say we have our Design Under
Test `pionic-test` (from my [PIO NIC project][10] and we want to run it on core
#47 (last CPU core on Enzians):

```console
$ sudo taskset -c 47 ./pionic-test
```

However, doing so isn't nearly enough: we also need to ensure that there are no
other tasks, both user-space and __kernel space__ (kthreads), running on core
#47.  Failing to evacuate these tasks will still result in the scheduler
stepping in, descheduling us, and scheduling these other tasks.  There are also
other concerns, like device IRQs, timer interrupts (_cough cough_), RCU
callbacks, bla bla.  Most of these can be moved off the core with some kernel
command-line options:

```
isolcpus=nohz,domain,managed_irq,47 rcu_nocbs=47 irqaffinity=0-46 kthread_cpus=0-46 rcu_nocb_poll
```

Many guides on the Internet detail on how to tune the kernel for real-time
applications (here's [one from the Ubuntu blog][11], for example).  I won't go
into the details of what each of these options mean since it's not related to
this article.

However, no matter how _quiet_ you try to make the kernel to be, the stock,
`-generic` kernel has its limits.  The default Ubuntu `-generic` kernel is
_tickful_ (I coined this as opposed to the more commonly used word
_tickless_--you'll see in a minute).  This means that even if _absolutely
nothing_ other than the user task is running on the core, and that you moved
all irrelevant IRQ processing etc. off the core, there still would be a
constant __timer interrupt__ (usually at 250 Hz; defined via the `HZ` config
option) going off on that core.  Measurements on the Enzian show that handling
this interrupt takes around _10 us_: not a lot of time, but enough to appear as
a large __tail latency__ if your application latency is sub-microsecond.

The kernel is _capable_ to be completely tickless [since 3.10][12], through the
compile-time config `CONFIG_NO_HZ_FULL`.  Enabling this option, along with
specifying `nohz_full=47` on the kernel command-line, will finally make this
250 Hz timer interrupt go away.  However, the feature still has some rough
edges, with potential performance impacts for specific workloads (since it
changes how time-keeping works), it is not generally deployed.  It certainly
isn't available in the Ubuntu archive for us to directly install.

### Why Ubuntu (vendor) kernel?

Hopefully that explains why I want a custom kernel.  But why do I have to use
the _Ubuntu_ kernel?  Well, yeah it's true that I can use the upstream tree
directly (it's the method for a custom kernel documented on the [Enzian
wiki][5]).  However, there are two catches:

- the stock Ubuntu kernel has a lot of patches; using the upstream tree would
  mean deviating _a lot_ from the vanilla setup (which is just stock Ubuntu)
- installing a upstream kernel is __unhygenic__: the installed kernel images
  and modules won't be tracked by `dpkg`, making it a pain to uninstall,
  reinstall, or package and redistribute

The distribution/vendor (Ubuntu) makes a nice kernel package that we should be
able to easily customize (_cough cough_) and rebuild.  This way, we can make
sure that there's as little divergence as possible from the _vanilla_ Ubuntu
kernel, for the sake of clean experiment results.

### Why cross-compile?

It stands that native-compiling is always easier than cross-compiling: no need
to carefully differentiate if you're compiling something that will execute on
the _host machine_ (i.e. the machine you're building __for__), or a tool that
you need during the build, for the _build machine_ (i.e. the machine you're
building __on__).  This is especially tricky when _dependencies_ are involved,
since binaries for wrong architecture won't execute (easily).

With that said, the old benefits of cross-compiling apply.  The Enzian has a
rather old [Cavium ThunderX-1][13] CPU that is not particularly fast.  In
addition, all machines are booted through iSCSI (5 GB image) with a NFS scratch
space, so storage is very limited (either slow or small).  It would be great if
we can cross-compile.

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
[8]: https://enzian.systems/
[9]: https://systems.ethz.ch/
[10]: https://github.com/KireinaHoro/enzian-pio-nic
[11]: https://ubuntu.com/blog/real-time-kernel-tuning
[12]: https://lwn.net/Articles/549580/
[13]: https://en.wikichip.org/wiki/cavium/microarchitectures/thunderx1
