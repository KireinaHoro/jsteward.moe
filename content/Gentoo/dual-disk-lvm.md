Title: Dual Disk LVM with Loopback Files
Date: 2018-02-05 12:00
Modified: 2018-02-05 12:00
Category: Gentoo
Tags: gentoo, lvm, sparc
Slug: dual-disk-lvm-with-loopback
Status: published

## The story

My SPARC Enterprise T5120 came with two 10000 RPM SAS HDDs, both with a labeled capacity of 146GB. Gentoo was installed on the first
hard drive, and thanks to the old SILO that was in charge of booting the system up, I have to keep a single-large-root partition
scheme. While the second disk seemed to be in some odd state (it had a block size of 528) and can't get recognized by Linux's SCSI
driver, I got it formatted with `sg_format`, turning it into a data disk with single partition on disk with ext4, and used it as the
default download location for Deluge, my BitTorrent client. So far, so good.

Yet 146GB is damn too tight these days, and soon it got filled up. Yet, the first disk, which was completely used as the root drive,
had around 130GB to spare. So is there a plan so that I can utilize _all_ the free space on the two disks, say, to combine them into
a _big new pool_?

## The solution

Fortunately, LVM comes to the rescue. It's trivial to create empty files, set them up as loopback devices, and make them considered pv's
by the system. Thanks to `truncate`, we can create files with big sizes, yet doesn't take up actual space.

### Creating the filesystem

```bash
cd /
truncate pool_member.img -s 135G # won't consume disk space
losetup /dev/loop0 /pool_member.img
cd /var/lib/deluge # mountpoint for /dev/sdb1
truncate pool_member.img -s 135G # won't consume disk space
losetup /dev/loop1 /var/lib/deluge/pool_member.img
pvcreate /dev/loop0
pvcreate /dev/loop1
vgcreate data /dev/loop0 /dev/loop1
lvcreate -i 2 -l +100%FREE -n download data
mkfs.ext4 /dev/data/download
mkdir -p /pool
mount /dev/data/download /pool
```

Check with `df -h` and we can see that there's a brand new filesystem mounted there, taking space from the two drives. What I had to do
next was simply moving the existing torrents over with Deluge's "Move Storage" feature.

### Automatically mounting the LV

Wait a second. Even though the volume is up and running, it would be too much labor having to do it manually every time the system reboots.
The following init script for OpenRC works well to solve this problem:

```bash
#!/sbin/openrc-run
# Copyright 1999-2018 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2

lv_file="/dev/data/download"

wait_file() {
    local file="$1"; shift
    local wait_seconds="${1:-10}"; shift # 10 seconds as default timeout

    until test $((wait_seconds--)) -eq 0 -o -e "$file" ; do sleep 1; done

    ((++wait_seconds))
}

depend() {
    need localmount
    before net
}

start() {
    ebegin "Starting mount local disk pool"
    losetup /dev/loop0 /pool_member.img
    losetup /dev/loop1 /var/lib/deluge/pool_member.img
    vgscan
    einfo "Waiting for LV to appear..."
    wait_file "$lv_file" 5 || {
        eend 1 "LV did not show up after waiting for 5 seconds"
    }
    mount /dev/data/download /pool
    eend $? "Failed to mount /pool"
}

stop() {
    ebegin "Stopping mount local disk pool"
    umount /pool
    vgchange -an /dev/data
    losetup -d /dev/loop0
    losetup -d /dev/loop1
    eend $? "Failed to unmount /pool"
}
```

Save it to `/etc/init.d/disk-pool`, give it `+x` permission, and add it to the default runlevel with

```
rc-update add disk-pool default
```

## Credit

Credit for this method goes to lilydjwg. Thanks!
