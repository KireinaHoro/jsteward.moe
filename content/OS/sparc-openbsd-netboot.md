Title: Netbooting OpenBSD on SPARC64
Date: 2020-9-6 20:35
Modified: 2020-9-6 20:35
Category: OS
Tags: os, sparc, openbsd
Slug: sparc-openbsd-netboot
Status: published

## What happened

The trusty SPARC machine I obtained from someone on the Gentoo mailing list quietly had its SAS 10k RPM HDD failed; the machine has been running Solaris 11.3 for over two years since I've blown up the [Gentoo setup]({filename}/Gentoo/dual-disk-lvm.md).  As the machine is co-located inside PKU and I do not have access to the server room, which is located on campus, due to the pandemic, the only possible way to revive the machine for probably some good is via netboot.  Fortunately, the SPARC OpenBoot PROM supports netbooting via RARP/TFTP (or DHCP) and I have other machines that can serve as a boot server in the same broadcast domain.  Let's get started!

## The boot protocol

The OpenBSD [netboot protocol `diskless(8)`](https://man.openbsd.org/diskless) explains the boot process quite well:

> When booting a system over the network, there are three phases of interaction between client and server:
> 
> - The PROM (or stage-1 bootstrap) loads a **boot program**.
> - The boot program loads a **kernel**.
> - The kernel does NFS mounts for root and swap.

The first and second phases, on SPARC, relies on the early environment provided by [OpenBoot](https://tldp.org/HOWTO/SPARC-HOWTO-14.html) for network access.  

### The first stage

The boot program loaded in this phase is the OpenBSD BOOT.  The first stage translate into the following concrete sequence:

- OpenBoot reads settings from NVRAM or console (by user input) and selects network as boot medium
- OpenBoot sends [RARP](https://en.wikipedia.org/wiki/Reverse_Address_Resolution_Protocol) requests as broadcast to obtain an IP address
- Assuming the host responding to RARP request is the boot server, OpenBoot pulls the relevant boot file via [TFTP](https://en.wikipedia.org/wiki/Trivial_File_Transfer_Protocol)
- OpenBoot executes the pulled boot file

The overall process is standardized as [RFC906](https://tools.ietf.org/html/rfc906), which dates back to 1984.  The limitations of this protocol is obvious: the TFTP server and RARP server are required to run on the same host (or some severe hackery would be needed).  A newer protocol, [BOOTP (RFC951)](https://tools.ietf.org/html/rfc951), is recommended for newer setups; we cannot deploy that here as I do not control the DHCP servers which, obviously, are run by the campus network operators.

### The second stage

The OpenBSD BOOT then uses Bootparams and NFS protocol to obtain the root filesystem information, loads kernel from root, and passes relevant information to the kernel.  Both protocols are part of the RPC protocol specified in [RFC5331](https://tools.ietf.org/html/rfc5531).  Specifically,

- OpenBSD BOOT reads root and swap settings via broadcasted Bootparams
- OpenBSD BOOT loads `bsd` and `bsd.rd` from root via NFS
- OpenBSD BOOT executes `bsd`, passing root and swap info

The kernel will then mount root and swap as specified during the later boot process.

## Preparing the boot server

The boot server mainly has two sets of responsibilities during the whole boot process:

- Respond to the broadcast and unicast requests of various protocols (RARP, TFTP, Bootparams, NFS)
- Serve the root and swap filesystems for the booted OpenBSD system

### Boot daemon configurations

Configuration files for relevant daemons are posted for future reference.

`/etc/ethers`:

```text
<mac address> <hostname>
```

`/etc/hosts`:

```text
<ip address> <hostname>
```

`/etc/bootparams`:

```text
<hostname> root=<server>:<root> swap=<server>:<swap>
```

`/etc/exports`:

```text
<root> <ip address>(rw,sync,no_subtree_check,no_root_squash,crossmnt,insecure)
<swap> <ip address>(rw,sync,no_subtree_check,no_root_squash,crossmnt,insecure)
```

`/etc/default/tftpd-hpa`:

```text
# /etc/default/tftpd-hpa

TFTP_USERNAME="tftp"
TFTP_DIRECTORY="/tftpboot"
TFTP_ADDRESS=":69"
TFTP_OPTIONS="--secure"
```

The OpenBSD BOOT file should reside in `/tftpboot` and symlinked to the output of the following:

```text
$ printf "%.2X%.2X%.2X%.2X\n" <ip address, separated with spaces>
```

### OpenBSD root filesystem preparation

Follow the section of *Upgrade without the install kernel* in the [OpenBSD Upgrade Guide: 6.6 to 6.7](https://www.openbsd.org/faq/upgrade67.html) to set up a working root filesystem on the NFS host.  Additional tips are listed below.

- The upgrade guide expects `bsdtar` for unpacking.  Make sure to keep the appropriate owners and groups.  Refer to `tar(1)` for details.
- To populate `/etc`, as most of the configuration files are out of `base`, unpack `/var/sysmerge/etc.tgz`.  Refer to `sysmerge(8)` for details.
- Run `/dev/MAKEDEV` to populate `/dev`.  If setting up on a Linux host, which is most likely the case, the generated script will not run as-is; for example, Linux `mknod` does not accept multiple targets at once.  Refer to [INSTALL.sparc64](https://ftp.openbsd.org/pub/OpenBSD/6.7/sparc64/INSTALL.sparc64), especially the _Net Boot or Diskless Setup Information_ section, for detailed instructions.  Rerun after system startup to fix permissions of the device nodes, which may be incorrect during creation on the Linux host.

The system should be ready now.