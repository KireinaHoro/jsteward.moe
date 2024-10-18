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
[native build below](#create-flavour-and-build-natively-on-enzian)), but
unfortunately none of the cross-compile approaches works.  I have submitted a
couple bug reports and will (hopefully) update accordingly when things change.

With that said, this whole process has been quite a journey: I learned a lot
about the Debian and Ubuntu packaging infrastructure.  This should serve as a
good _layman's guide_ for distribution kernel hacking (at least for Ubuntu).
It also gives good starting knowledge for creating my own, custom Debian
packages.

[TOC]

## Motivation

### Why custom kernel?

The core idea is very simple: when doing performance measurements for a
user-space application, one would want as little disruption as possible.  This
is traditionally handled by _pinning_ a task to a specific CPU core, to avoid
the scheduler moving it willy-nilly across cores.  Say we have our Design Under
Test `pionic-test` (from my [PIO NIC project][10] and we want to run it on core
\#47 (last CPU core on Enzians):

```console
$ sudo taskset -c 47 ./pionic-test
```

However, doing so isn't nearly enough: we also need to ensure that there are no
other tasks, both user-space and __kernel space__ (kthreads), running on core
\#47.  Failing to evacuate these tasks will still result in the scheduler
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
changes how time-keeping works), it is not widely deployed.  It certainly isn't
available in the Ubuntu archive for us to directly install.

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

## Create flavour and build natively on Enzian

### "Shallow-fork" the vendor tree

We start with the [focal kernel Git tree][14] to add our changes.  The full
kernel tree history is huge, so we would do a shallow clone:

```console
$ git clone https://git.launchpad.net/\~ubuntu-kernel/ubuntu/+source/linux/+git/focal/ linux-focal -b Ubuntu-5.4.0-200.220 --depth=1
```

However, GitLab doesn't support pushing shallow clones of repositories.  We
need a bit of black magic, namely with the power of `git replace` [documented
in the Git book][6].  The idea is that we create a brand-new tree based on the
shallow `HEAD` with the `commit-tree` command; root of this tree can later be
replaced with the full history if we need it.  I duplicate the exact commands
here for future reference:

```console
$ git commit-tree Ubuntu-5.4.0-200.220^{tree} << EOF
> Forked from Ubuntu-5.4.0-200.220 in focal
>
> Get full history from upstream focal tree at
> https://git.launchpad.net/~ubuntu-kernel/ubuntu/+source/linux/+git/focal/ ;
> Instructions at https://git-scm.com/book/en/v2/Git-Tools-Replace
> EOF
8adb6ccde3615be4787b1583d4cb231d123d0fd1
$ git checkout -b 5.4-tickless 8adb6ccde3615be4787b1583d4cb231d123d0fd1
...
$ git push -u gitlab <department gitlab url>
```

As described by a [StackOverflow answer][15]:

> Say that I want to effectively “squash” all the commits in the repo down to a
> single commit. But “squash” is a rebase operation which is excessive since it
> combines changes, and I don’t need to combine any changes since I already
> know what snapshot I want—the current one.

### Set up kernel flavour

We need to decide _where_ to put our tickless modifications:

- either, as a _local update_ to the `-generic` kernel
    - this would result in the same package name `linux-image-unsigned-5.4.0-200-generic`
      with a version number like `5.4.0-200.220+pengxu~tickless`
- or, as a __new flavour__ alongside the `-generic` flavour
    - this would result in a _new_ package `linux-image-unsigned-5.4.0-200-tickless`,
      with a version number like `5.4.0-200.220+pengxu`

@shankerwangmiao suggests that the second one is the way to go: the first
approach is abusing the version number and will result in the kernel being
replaced by a newer major version update.

I adopted the new flavour approach.  The [necessary changes][7] are recorded in
the Git repo of my fork, but here's a brief list of the changes needed:

- create `debian.master/control.d/vars.tickless` to declare metadata of the
  flavour (used to generate the [package control file][16])
- declare our `tickless` flavour in `debian.master/rules.d/arm64.mk`
    - make sure that your flavour defines `build_image` and `kernel_file`!
- update configs
    - `fakeroot debian/rules clean` to generate the necessary rule files
    - `fakeroot debian/rules editconfigs` to launch `menuconfig` and update
      `debian.master/config/annotations`
        - Ubuntu deviates from Debian and created this annotation format,
          caused me a lot of headache
- update `changelog`
    - use the `dch` helper: `DEBEMAIL='Pengcheng Xu <email>' dch -c debian.master/changelog -l+pengxu`

`debian/rules` will require some tools to execute correctly; refer to [the
official guide][1] to install them.  The new `-tickless` kernel flavour should
now be ready.  To see if everything is set up correctly, commit, clean the
tree, and build the kernel natively:

```console
$ git add debian.master && git commit -m '...'
$ git clean -dfx # to get rid of all generated files
$ fakeroot debian/rules clean
$ fakeroot debian/rules binary-headers binary-tickless binary-perarch
```

The above should build the kernel, headers, and modules.  As @shankerwangmiao
and @Harry_Chen pointed out and also stated in the [Debian maintainer's
guide][17], however, it's not recommended to directly call the rules.  The
correct way is to use `dpkg-buildpackage`, to either do a full rebuild, or run
a couple targets:

```bash
# full rebuild
dpkg-buildpackage -us -uc -B
# run some targets in the rule; theoretically equivalent to invoking debian/rules above
dpkg-buildpackage -us -uc -d -T 'binary-headers,binary-tickless,binary-perarch' --as-root
```

It's recommended to rebuild everything, instead of running only selected
target.  The reason is that, it's easy to produce an _uninstallable_ subset of
packages by missing a target.  This happened when I forgot to call
`binary-perarch`: `binary-tickless` produced a flavour-dependent
`linux-tools-5.4.0-200-tickless`, that depends on the _per-architecture_ (i.e.
flavour-independent) `linux-tools-5.4.0-200`.  Since the `5.4.0-200` packages
are not yet available on the archive, this resulted in the flavoured
`linux-tools` being uninstallable.

Check the outer directory for the resulting `.deb` packages, to be installed on
Enzian:

```console
$ ls -sh ../*.deb
1.3M ../linux-buildinfo-5.4.0-200-tickless_5.4.0-200.220+pengxu_arm64.deb
1.8M ../linux-headers-5.4.0-200-tickless_5.4.0-200.220+pengxu_arm64.deb
 12M ../linux-headers-5.4.0-200_5.4.0-200.220+pengxu_all.deb
 13M ../linux-image-unsigned-5.4.0-200-tickless_5.4.0-200.220+pengxu_arm64.deb
 56M ../linux-modules-5.4.0-200-tickless_5.4.0-200.220+pengxu_arm64.deb
900K ../linux-tools-5.4.0-200-tickless_5.4.0-200.220+pengxu_arm64.deb
5.1M ../linux-tools-5.4.0-200_5.4.0-200.220+pengxu_arm64.deb
```

## Cross compile

Now that we can build our kernel flavour natively, we can start attempting to
cross-compile it.  I have to reiterate here: none of the following actually
worked reliably!  Even though `sbuild` managed to produce `.deb` packages in
the end, I don't think they are built correctly and didn't bother to test the
resulting packages--something is fundamentally wrong with the build.  Don't say
that I told you it would work :)

With that said, I'm fairly confident that I am on the right track.  Provided
that the Ubuntu kernel team rework the dependency declarations, there's quite
good chance that my approach will work.

### Attempt \#1: invoking the rule with `arch=arm64`

I bumped into this by searching for `arch` in all the Makefiles inside
`debian/`--documentation was really scarce on how to cross compile the Ubuntu
kernel after all.  Quoting from `debian/rules.d/0-common-vars.mk`:

```makefile
#
# Detect invocations of the form 'fakeroot debian/rules binary arch=armhf'
# within an x86'en schroot. This only gets you part of the way since the
# packaging phase fails, but you can at least compile the kernel quickly.
#
arch := $(DEB_HOST_ARCH)
ifneq ($(arch),$(DEB_HOST_ARCH))
    CROSS_COMPILE ?= $(shell dpkg-architecture -a$(arch) -qDEB_HOST_GNU_TYPE -f 2>/dev/null)-
endif
```

At this point I understood neither what an `schroot` is, nor how the build
would fail.  So I ran the following:

```console
$ fakeroot debian/rules clean
$ fakeroot debian/rules binary-headers binary-tickless binary-perarch arch=arm64
```

The kernel did seem to compile--I saw lots of familiar `CC [M] ....` lines roll
by, but what came as a surprise is that the rule didn't generate a `*.deb`
package for the kernel image:

```plain

```

Seems like not all required `dpkg` environment variables for cross-compiling
were set correctly, resulting in `dpkg-*` skipping the `arm64` packages.  This
is the time @shankerwangmiao pointed out that it's time to try
`dpkg-buildpackage -aarm64`--a lot of times it "just works" automagically.

### Attempt \#2: `dpkg-buildpackage`

The recommendation is definitely not unfounded.  Quoting from
`debian/rules.d/0-common-vars.mk` again:

```makefile
#
# Detect invocations of the form 'dpkg-buildpackage -B -aarmhf' within
# an x86'en schroot. This is the only way to build all of the packages
# (except for tools).
#
ifneq ($(DEB_BUILD_GNU_TYPE),$(DEB_HOST_GNU_TYPE))
    CROSS_COMPILE ?= $(DEB_HOST_GNU_TYPE)-
endif
```

This time we do get the

- attempt the same thing for building directly on Enzian
- command: `dpkg-buildpackage -uc -us -d -a arm64 -T 'binary-headers,binary-tickless,binary-perarch' --as-root`
- since we are not running in a chroot, `dh_shlibdeps` picked up the wrong `libc6` version
    - @Harry_Chen

### Attempt \#3: set up [sbuild][2] and a focal chroot

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

ubuntu kernel still doesn't cross compile: mix-up between build and host dependencies
- `libssl-dev` missing on build prevents `sign-file` from building
- other ones like `pahole` also fails to execute on build (host version is pulled in), but does not abort build
    - does this affect correctness?

- Asked on #kernel:ubuntu.com (Matrix), Timo Aaltonen (@tjaalton:ubuntu.com) confirmed that this is not ideal and I should file a bug
    - &lt;bug url&gt;

## Emulated native build with `qemu-user-static` and `binfmt_misc`

Timo from Ubuntu used a arm64 schroot (foreign)--therefore it's emulated "native" build

Theoretically would work fine, supported by `mmdebstrap`, but lots of lost performance.  Probably the way to go for now

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
[14]: https://git.launchpad.net/~ubuntu-kernel/ubuntu/+source/linux/+git/focal
[15]: https://stackoverflow.com/a/76102264/5520728
[16]: https://www.debian.org/doc/debian-policy/ch-controlfields.html
[17]: https://www.debian.org/doc/manuals/maint-guide/build.en.html
