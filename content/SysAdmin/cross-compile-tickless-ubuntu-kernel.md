Title: Cross-compiling a Tickless Ubuntu Kernel
Date: 2024-10-16T11:55+02:00
Modified: 2024-10-21T11:39+02:00
Category: SysAdmin
Tags: ubuntu, linux, kernel
Slug: cross-compile-tickless-ubuntu-kernel
Status: published

## Preface

This article documents the trial-and-error process of me trying to
cross-compile the Ubuntu kernel for `arm64` for use with [Enzians][8] at the
[Systems Group at ETH][9].  So far building natively on the Enzians work (see
[native build below](#create-flavour-and-build-natively-on-enzian)), but
unfortunately none of the cross-compile approaches produce reliable `.deb`
packages.  I have submitted a couple bug reports and will (hopefully) update
accordingly when things change.

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
_tickful_ (I coined this as opposed to the more commonly used word _tickless_
-- you'll see in a minute).  This means that even if _absolutely nothing_ other
than the user task is running on the core, and that you moved all irrelevant
IRQ processing etc. off the core, there still would be a constant __timer
interrupt__ (usually at 250 Hz; defined via the `HZ` config option) going off
on that core.  Measurements on the Enzian show that handling this interrupt
takes around _10 us_: not a lot of time, but enough to appear as a large __tail
latency__ if your application latency is sub-microsecond.

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
  - @Harry_Chen mentioned that the upstream Makefiles are _capable_ of
    producing `.deb` packages; however due to the fear that they might not
    conform to Ubuntu conventions, I didn't explore in this direction

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

I tested these packages on the Enzian -- they seem to work just fine.

## Cross compile

Now that we can build our kernel flavour natively, we can start attempting to
cross-compile it.  I have to reiterate here: __none of the following__ actually
worked (i.e. produced packages that _could_ work)!  Even though `sbuild`
managed to produce `.deb` packages in the end, I don't think they are built
correctly and didn't bother to test the resulting packages -- something is
fundamentally wrong with the build.  Don't say that I told you it would work :)

With that said, I'm fairly confident that I am on the right track.  Provided
that the Ubuntu kernel team rework the dependency declarations, there's quite
good chance that `sbuild` will be able to produce correct packages.

### Attempt \#1: invoking the rule with `arch=arm64`

I bumped into this by searching for `arch` in all the Makefiles inside
`debian/` -- documentation was really scarce on how to cross compile the Ubuntu
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

The kernel did seem to _compile_ -- I saw lots of familiar `CC [M] ....` lines
roll by.  However, I was hit too many times with missing dependencies during
the build, including this very cryptic one about Python:

```console
checking for python3... python3
checking for python version... 3.1
checking for python platform... linux
checking for python script directory... ${prefix}/local/lib/python3.10/dist-packages
checking for python extension module directory... ${exec_prefix}/local/lib/python3.10/dist-packages
configure: error: "Python >= 3.4 is required"

Building module:
cleaning build area...(bad exit status: 2)
make -j12 KERNELRELEASE=5.4.0-200-tickless...(bad exit status: 2)
Error! Bad return status for module build on kernel: 5.4.0-200-tickless (x86_64)
Consult /local/home/pengxu/work-local/bare-test/bare-rules-build/debian/build/build-tickless/___________dkms/build/zfs/0.8.3/build/make.log for more information.
DKMS make.log for zfs-0.8.3 for kernel 5.4.0-200-tickless (x86_64)
Sat Oct 19 08:30:07 CEST 2024
make[1]: Entering directory '<<DKMSDIR>>/build/zfs/0.8.3/build'
make[1]: *** No targets specified and no makefile found.  Stop.
make[1]: Leaving directory '<<DKMSDIR>>/build/zfs/0.8.3/build'
make: *** [debian/rules.d/2-binary-arch.mk:234: install-tickless] Error 1
```

Apparently the build rules didn't recognize that Python 3.10 is newer than 3.4;
I just gave up at this point.  It didn't come as a surprise is that the rule
didn't generate useful `*.deb` kernel packages.

In hindsight this looked awfully apparent that I had to use a `chroot`, such
that we have all the dependencies fixed to the version that the rule expects.
In fact the above error is differnet from the one I was looking at back then --
`dpkg-deb` complained about all packages being skipped, so I thought maybe not
all required `dpkg` environment variables for cross-compiling were set
correctly.  Together with the comment from @shankerwangmiao that usually
`dpkg-buildpackage -aarm64` "just works" automagically, I went on with my
second attempt.

### Attempt \#2: `dpkg-buildpackage`

The recommendation of using `dpkg-buildpackage` is definitely not unfounded.
Quoting from `debian/rules.d/0-common-vars.mk` again:

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

So we attempt to run the same command as on Enzian, with the addition of
`-aarm64` to specify cross-compiling:

```console
$ dpkg-buildpackage -uc -us -d -aarm64 -T 'binary-headers,binary-tickless,binary-perarch' --as-root
```

This time we do get some `.deb` packages, namely the _per-arch_
`linux-headers`, flavoured `linux-headers-tickless`, `linux-image-unsigned`,
and `linux-modules-tickless`.  However, both the _per-arch_ and flavoured
`linux-tools` are missing, meaning that some packages didn't build.  Even
worse, the built packages have bad dependency versions:

```console
$ dpkg -I ../linux-headers-5.4.0-200-tickless_5.4.0-200.220+pengxu_arm64.deb
[...]
 Package: linux-headers-5.4.0-200-tickless
 Source: linux
 Version: 5.4.0-200.220+pengxu
 Architecture: arm64
[...]
 Depends: linux-headers-5.4.0-200, libc6 (>= 2.34), libssl3 (>= 3.0.0~~alpha1)
[...]
```

Ubuntu focal (20.04 LTS) doesn't have `libc6 (>= 2.34)` at all!  The correct
dependencies, from packages built natively on the Enzian, should be:

```console
dpkg -I debs/linux-headers-5.4.0-200-tickless_5.4.0-200.220+pengxu_arm64.deb
[...]
 Package: linux-headers-5.4.0-200-tickless
 Source: linux
 Version: 5.4.0-200.220+pengxu
 Architecture: arm64
[...]
 Depends: linux-headers-5.4.0-200, libc6 (>= 2.17), libssl1.1 (>= 1.1.0)
[...]
```

Turns out my build machine is running jammy (22.04 LTS) instead of 20.04, and
`dh_shlibdeps` captured the wrong, newer symbol versions, thus generating the
newer `libc6` and `libssl` dependencies.  This was pointed out by @Harry_Chen
-- now it is really apparent that I have to use a `chroot` for building.

### Attempt \#3: set up [sbuild][2] and a focal chroot

Debian offers pbuilder and sbuild for building packages in a clean fashion.
They are said to have very similar feature sets, but it seems like sbuild
supports a pure _rootless_ operation through `unshare` using `mmdebstrap`.
This will be handy if I want to use the build farm from the Enzian project
(where I don't have root access), so I went with sbuild.

The steps to set up sbuild with `mmdebstrap` is mostly already documented on
[the Debian wiki page][2], so I'll just note down the catches that I wasted
some time on:

- `mmdebstrap` shipped with Ubuntu 22.04 checks for groupname instead of
  username in `/etc/subgid`
    - ETH LDAP have different user and group name (`pengxu` vs `pengxu-group`)
    - fixed by [upstream][3] but not included in 22.04 (0.8.4-1ubuntu0.1)
    - temporary fix: list both `pengxu` and `pengxu-group` in `/etc/subgid` to
      satisfy `mmdebstrap`; I've opened a [bug for Ubuntu][21]
- the main Ubuntu archive (`archive.ubuntu.com/ubuntu`) does not include `arm64`
    - `arm64` is in the ports archive (`ports.ubuntu.com/ubuntu-ports`)
    - fix by supplying the following custom `sources.list` to `mmdebstrap`

```text
# ~/my-sources.list
deb [arch=amd64] http://archive.ubuntu.com/ubuntu/ focal main restricted universe multiverse
deb [arch=amd64] http://archive.ubuntu.com/ubuntu/ focal-updates main restricted universe multiverse
deb [arch=amd64] http://archive.ubuntu.com/ubuntu/ focal-backports main restricted universe multiverse
deb [arch=amd64] http://security.ubuntu.com/ubuntu/ focal-security main restricted universe multiverse

deb [arch=arm64] http://ports.ubuntu.com/ubuntu-ports/ focal main restricted universe multiverse
deb [arch=arm64] http://ports.ubuntu.com/ubuntu-ports/ focal-updates main restricted universe multiverse
deb [arch=arm64] http://ports.ubuntu.com/ubuntu-ports/ focal-backports main restricted universe multiverse
deb [arch=arm64] http://ports.ubuntu.com/ubuntu-ports/ focal-security main restricted universe multiverse
```

- do not use the `buildd` profile: `apt-get` is missing yet `mmdebstrap`
  depends on it
- `sbuild` on Ubuntu 22.04 doesn't recognise `tar.zst`-compressed tarballs,
  despite the [Debian wiki][2] recommending it
    - Using lz4 since it's the fastest according to [this benchmark][4]

Final commands:

```console
$ sudo apt install lz4 mmdebstrap uidmap sbuild
$ echo "pengxu:1000000:65536\npengxu-group:1000000:65536" | sudo tee -a /etc/subgid
$ mkdir -p ~/.cache/sbuild
$ mmdebstrap --arch="amd64 arm64" focal ~/.cache/sbuild/focal-amd64.tar.lz4 ~/my-sources.list
$ sbuild-update --chroot-mode=unshare -udcar # test access by sbuild
```

We should now be able to do `sbuild --host=arm64 -d focal` to cross-compile the
entire kernel package...  only if would be that easy :)  This time the build
process fails really early, when compiling the `scripts/sign-file` tool shipped
by the Linux kernel upstream.  It turns out that the Ubuntu kernel mixes build
and host dependencies without marking them correctly with `:native` (as
described in [the Debian cross-compile guidelines]).  The Debian kernel
(correctly) [defines `Build-Depends` as follows][19]:

```plain
Section: kernel
[...]
Build-Depends:
[...]
# used by upstream to build signing tools and to process certificates
 libssl-dev:native <!pkg.linux.nokernel>,
 libssl-dev <!pkg.linux.notools>,
```

You can see the correct way here is to depend on the __build-native__
`libssl-dev` for building the `sign-file` tool, unless the `pkg.linux.nokernel`
profile is selected (meaning that we are not building the kernel after all).
We would depend on the __host-native__ `libssl-dev` when we are building
`linux-tools`, unless the `pkg.linux.notools` profile is selected.  In
comparison, Ubuntu's kernel rules does [something way cruder][20]:

```plain
[...]
Build-Depends:
[...]
 libssl-dev <!stage1>,
```

We can see that Ubuntu didn't differentiate between __build__ and __host__ at
all when declaring build dependencies.  The same issue is also present for
other tools like `pahole` -- they fail to execute on the build machine due to
the incorrect version being installed.  Those failure didn't fail the entire
build, meaning that a small patchwork for `libssl-dev` allowed the build to
actually produce `.deb` packages.  However, I really wouldn't trust the
packages compiled this way.

I asked on `#kernel:ubuntu.com` on Matrix about if this lack of awareness of
cross-compiling is intended.  The answer from Timo Aaltonen
(`@tjaalton:ubuntu.com`), one of Ubuntu's core devs, is no:

> __Timo__: ack. btw, do file a bug against the kernel so it's not forgotten. I
> don't think there's a reason why this is like it is. We might just as well do
> what debian does here

So I've submitted [a bug][22] for this.

## Emulated native build with `qemu-user-static` and `binfmt_misc`

My conversation with Timo actually revealed the fact that a separate route of
building the kernel on a beefy amd64 machine being possible:

> __Timo__: then again I created a schroot for armhf, so you're using the amd64
> chroot? <br />
> __Me__: ah yes, I have a focal-amd64. If you have a schroot for armhf, does
> that mean you're using qemu-user with binfmt? <br />
> __Timo__: probably

An `armhf` schroot on an `amd64` build machine is essentially what I would call
_emulated native build_ -- execution of `armhf` binaries is emulated through
`qemu-user-static` (static since we are inside a chroot).  `mmdebstrap` has
support for this pattern.  Install necessary dependencies and set up chroot

```console
$ sudo apt install binfmt-support qemu-user-static
$ mmdebstrap --arch=arm64 focal ~/.cache/sbuild/focal-arm64.tar.lz4
```

After the chroot is set up, we can then request sbuild to build with __both
build and host set to arm64__ via `--arch=arm64`:

```console
$ sbuild --arch=arm64 -d focal
```

However, it seems like the kernel rule lists several old `Build-Depends`
packages that are not in the focal archive any more:

```plain
The following packages have unmet dependencies:
 sbuild-build-depends-main-dummy : Depends: dh-systemd but it is not installable
                                   Depends: dwarves but it is not installable
                                   Depends: xmlto but it is not installable
                                   Depends: docbook-utils but it is not installable
                                   Depends: fig2dev but it is not installable
                                   Depends: asciidoc but it is not installable
                                   Depends: python3-sphinx-rtd-theme but it is not installable
```

I'm not sure how to proceed here any more.  Looks like the [newer kernel
trees][23] don't have these stale dependencies...

## Closing remarks

I've explored in somewhat detail how the Ubuntu kernel rules work, opened some
bugs, and found a plausible way to proceed.  Let's stay tuned on the bugs!

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
[18]: https://wiki.debian.org/Multiarch/HOWTO#When_to_use_:native_and_when_to_use_:any.3F
[19]: https://salsa.debian.org/kernel-team/linux/-/blob/8941549ed01ecdd8b9d2f84f2fb1d46507b76861/debian/templates/source.control.in#L19-21
[20]: https://github.com/KireinaHoro/linux-focal-variants/blob/8adb6ccde3615be4787b1583d4cb231d123d0fd1/debian.master/control.stub.in#L28
[21]: https://bugs.launchpad.net/ubuntu/+source/mmdebstrap/+bug/2085004
[22]: https://bugs.launchpad.net/ubuntu/+source/linux/+bug/2085030
[23]: https://git.launchpad.net/~ubuntu-kernel/ubuntu/+source/linux/+git/noble/tree/debian.master/control.stub.in
