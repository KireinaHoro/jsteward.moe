Title: Go on Gentoo SPARC
Date: 2018-01-22 16:00
Modified: 2018-01-25 14:00
Category: Go
Tags: golang, gentoo, sparc
Slug: go-on-gentoo-sparc
Status: published

## Preface

Gc (Go's most widely-used compiler) isn't available for `GOOS=linux && GOARCH=sparc`
(Gentoo SPARC) for now; what makes matters worse is that Gccgo (`sys-devel/gcc[go]`)
is not working on Gentoo (it hangs in early initialization). Debian Ports comes to
the rescue, as although no Gc as well, their Gccgo (at least `gccgo-6`; `gccgo-7` panics
in early stages) is working. Yet Debian's SPARC port is on architecture `sparc64`, which
means it'll run on a Gentoo kernel (UltraSPARC T2 requires a 64bit kernel), yet the
executables it creates won't run outside without some tricks. (Gentoo SPARC has 32bit userland)

## Set up Debian Ports environment

Install debootstrap:

```bash
emerge --ask --verbose dev-util/debootstrap
```

Make the debian root and create the chroot with `debootstrap`:

```bash
mkdir -p /var/debian/
debootstrap --arch=sparc64 --variant=buildd --verbose sid /var/debian/ https://deb.debian.org/debian-ports
```

Download the required keychain package. Chroot into the new debian environemnt, install keychain, and install required packages:

```bash
cd /var/debian/root
wget http://deb.debian.org/debian-ports/pool/main/d/debian-ports-archive-keyring/debian-ports-archive-keyring_2018.01.05_all.deb
chroot /var/debian /bin/su
chsh -s /bin/bash
dpkg -i /root/debian-ports-archive-keyring_2018.01.05_all.deb
apt update
apt install gccgo-6
```

Symlink the required go tools, make the GOPATH, and set it upon entering the chroot:

```bash
for a in go{,fmt}; do ln -sf /usr/bin/$a-6 /usr/bin/$a; done
mkdir -p /root/go
echo "export GOPATH=/root/go" >> /root/.bashrc
```

Exit the chroot, enter it once again, and verify that everything's working:

```bash
exit
chroot /var/debian /bin/su
go env
```

Test the toolchain via a simple `Hello, world!`:

```bash
cd
cat > helloworld.go << EOF
package main

import "fmt"

func main() {
    fmt.Println("Hello, world!")
}
EOF
go run helloworld.go
go build helloworld.go
./helloworld
```

## Set up Gentoo to use the executables from Debian chroot

Now that we can produce executables, we need to set up the Gentoo system to be
able to use the executables from Debian chroot. Debian has 64bit libc:

```plain
root@hikari:~# ldd helloworld
        libgo.so.9 => /usr/lib/sparc64-linux-gnu/libgo.so.9 (0xffff800100230000)
        libm.so.6 => /lib/sparc64-linux-gnu/libm.so.6 (0xffff8001015ac000)
        libgcc_s.so.1 => /lib/sparc64-linux-gnu/libgcc_s.so.1 (0xffff800101794000)
        libc.so.6 => /lib/sparc64-linux-gnu/libc.so.6 (0xffff8001018a8000)
        libpthread.so.0 => /lib/sparc64-linux-gnu/libpthread.so.0 (0xffff800101b18000)
        /lib64/ld-linux.so.2 (0xffff800100000000)
```

We need to copy those to the Gentoo host's `/lib64` and add it to `ld`'s search paths.

```bash
mkdir -p /lib64
for a in /usr/lib/sparc64-linux-gnu/libgo.so.9 /lib/sparc64-linux-gnu/{libm.so.6,libgcc_s.so.1,libc.so.6.libpthread.so.0} /lib64/ld-linux.so.2; do cp -Lv /var/debian$a /lib64/$(basename $a); done
cp -Pv /var/debian/lib/sparc64-linux-gnu/libnss* /lib64 # needed for proper user / dns support
sed -i -e 's|/lib:/usr/lib|/lib:/lib64:/usr/lib|' /etc/env.d/00basic
env-update
```

We can now check if the executable works outside the chroot:

```bash
cd /var/debian/root
ldd helloworld
./helloworld
```

If any libraries are missing, we need to copy it over (to `/lib64`) and re-generate
`ld.so.cache` with `env-update`. From this point we're able to compile the Go source code in
the Debian chroot, and copy it over for use.

## Extra setup for ease of use

Copying the executable outside the chroot outside every time is exhausting. The following setup
will ease the process of compiling source and using the executable.

Set up fstab entries for the debian chroot, so that it will be ready for use right after
boot. Failing to mount system psuedo-filesystems (especially `/proc`) will result in
mysterious errors with `libbacktrace`.

```plain
# debian chroot mounts
/dev /var/debian/dev none defaults,rbind,rslave 0 0
/sys /var/debian/dev none defaults,rbind,rslave 0 0
/proc /var/debian/proc none defaults,rbind,rslave 0 0
# mount to expose the executables built to the system outside
/var/debian/root/go/bin /usr/local/go/bin none defaults,bind 0 0
```

The last entry exposes `${GOPATH}/bin` inside the debian chroot to the system
outside, so that we can add `/usr/local/go/bin` to `PATH`, and easily use them
outside (as we have set up appropriate `libc` outside).

Add the `/usr/local/go/bin` to `PATH`:

```bash
echo "PATH=\"/usr/local/go/bin\"\nROOTPATH=\"/usr/local/go/bin\"" | sudo tee /etc/env.d/40debian-golang
env-update
```

And add the following alias to your shell config (`.bashrc` or `.zshrc`):

```bash
alias gobuild='sudo chroot /var/debian /bin/bash --login'
```

We can now issue `gobuild` from Gentoo, go into the Debian chroot, issue

    go get path/to/your/great/package

to install your binary, and then you can access them outside the chroot as well,
thanks to the bind mount and the `PATH` settings.

## Credits

The method to resolve the incompatiable libc libraries comes from lilydjwg, while the suggestion
of installing the keychain package instead of importing raw keys comes from zhsj. Thanks.
