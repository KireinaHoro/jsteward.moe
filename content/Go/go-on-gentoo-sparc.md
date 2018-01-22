Title: Go on Gentoo SPARC
Date: 2018-01-22 16:00
Modified: 2018-01-22 16:00
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

```
emerge --ask --verbose dev-util/debootstrap
```

Make the debian root and create the chroot with `debootstrap`:

```
mkdir -p /var/debian/
debootstrap --arch=sparc64 --variant=buildd --verbose sid /var/debian/ https://deb.debian.org/debian-ports
```

Download the required apt keys. Chroot into the new debian environemnt, install keys, and install required packages:

```
gpg --keyserver pgp.mit.edu --recv-keys 06AED62430CB581C
gpg --armor --export 06AED62430CB581C > /var/debian/root/06AED62430CB581C.asc
chroot /var/debian /bin/su
chsh -s /bin/bash
apt-key add /root/06AED62430CB581C.asc
apt update
apt install gccgo-6
```

Symlink the required go tools, make the GOPATH, and set it upon entering the chroot:

```
for a in go{,fmt}; do ln -sf /usr/bin/$a-6 /usr/bin/$a; done
mkdir -p /root/go
echo "export GOPATH=/root/go" >> /root/.bashrc
```

Exit the chroot, enter it once again, and verify that everything's working:

```
exit
chroot /var/debian /bin/su
go env
```

Test the toolchain via a simple `Hello, world!`:

```
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

> root@hikari:~# ldd helloworld
>         libgo.so.9 => /usr/lib/sparc64-linux-gnu/libgo.so.9 (0xffff800100230000)
>         libm.so.6 => /lib/sparc64-linux-gnu/libm.so.6 (0xffff8001015ac000)
>         libgcc_s.so.1 => /lib/sparc64-linux-gnu/libgcc_s.so.1 (0xffff800101794000)
>         libc.so.6 => /lib/sparc64-linux-gnu/libc.so.6 (0xffff8001018a8000)
>         libpthread.so.0 => /lib/sparc64-linux-gnu/libpthread.so.0 (0xffff800101b18000)
>         /lib64/ld-linux.so.2 (0xffff800100000000)

We need to copy those to the Gentoo host's `/lib64` and add it to `ld`'s search paths.

```
mkdir -p /lib64
for a in /usr/lib/sparc64-linux-gnu/libgo.so.9 /lib/sparc64-linux-gnu/{libm.so.6,libgcc_s.so.1,libc.so.6.libpthread.so.0} /lib64/ld-linux.so.2; do cp -Lv /var/debian$a /lib64/$(basename $a); done
cp -Pv /var/debian/lib/sparc64-linux-gnu/libnss* /lib64 # needed for proper user / dns support
sed -i -e 's|/lib:/usr/lib|/lib:/lib64:/usr/lib|' /etc/env.d/00basic
env-update
```

We can now check if the executable works outside the chroot:

```
cd /var/debian/root
ldd helloworld
./helloworld
```

If any libraries are missing, we need to copy it over (to `/lib64`) and re-generate
`ld.so.cache` with `env-update`. From this point we're able to compile the Go source code in
the Debian chroot, and copy it over for use.
