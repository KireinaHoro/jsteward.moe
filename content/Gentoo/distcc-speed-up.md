Title: Using distcc to speed up builds on phone
Date: 2018-07-16 2:00
Modified: 2018-07-16 2:00
Category: Gentoo
Tags: gentoo, gsoc
Slug: distcc-speed-up
Status: published

## Preface

Compiling is the main source of time consumption on a Gentoo system, and Portage-powered Android is of no exception.  Gentoo packages can leverage [Distcc](https://wiki.gentoo.org/wiki/Distcc) to significantly speed up builds on slow machines with the aid of a powerful machine.  For utilization in the Portage-powered Android project, we need to enable cross-compiling support for distcc.  This article is a digest of the following two Gentoo Wiki articles, concisely logging the process to use distcc properly:

  * [Distcc](https://wiki.gentoo.org/wiki/Distcc)
  * [Distcc/Cross-Compiling](https://wiki.gentoo.org/wiki/Distcc/Cross-Compiling)

## Setup on the machine running `emerge`

`Distcc` functions as a client handing out jobs to servers on the machine running `emerge`.  Emerge distcc and Portage's distcc support, where `$REMOTE_CORES` is the number of cores available on the remote helper machine:

```bash
emerge sys-devel/distcc
N=$(($(nproc) + $REMOTE_CORES + 1))
M=$(($(nproc) + 2))
echo "MAKEOPTS=\"-j$N -l$M\"
FEATURES=\"distcc\"" >> /etc/portage/make.conf
```

Then configure distcc itself.  As distcc does not use authentication (which would significantly slow down builds), it is recommended to have the build machine and the emerge machine in the same LAN and deploy proper firewall rules or ACLs.  Run the following and substitute `192.168.1.1` with the IP address of your helper machine:

    distcc-config --set-hosts "192.168.1.1"

A special mode called "pump mode" for distcc which offloads the preprocessing work to the helper box may also be used, which may even speed up the build speed.  In some cases (e.g. `sys-devel/llvm`) the pump server may fail to determine which headers to send to the helper box, so it may need to be disabled in some occasions.  To enable pump mode:

    distcc-config --set-hosts "192.168.1.1,cpp,lzo"
    sed -i -e 's/^FEATURES="distcc"$/FEATURES="distcc distcc-pump"/' /etc/portage/make.conf

As what distcc does is proxying compiler calls to the helper server, and we're doing cross-compile here, we need to correctly set up a wrapper script for compiler symlinks that calls the correct `CHOST`.  Put the following script into `/usr/local/sbin/distcc-fix` and give it executable permission:

```bash
#!/bin/bash

# Clang aware, now your >chromium-65 ebuilds will use distcc just like before ;)
# We extract $TUPLE from make.conf to avoid editing the script for each architecture.
TUPLE=$(portageq envvar CHOST)
GCC_VER=$(gcc-config -c|cut -d "-" -f5)
CLANG_VER=$(clang --version|grep version|cut -d " " -f3|cut -d'.' -f1,2)
cd /usr/lib/distcc/bin
rm cc c++ gcc g++ gcc-${GCC_VER} g++-${GCC_VER} clang clang++ clang-${CLANG_VER} clang++-${CLANG_VER} ${TUPLE}-wrapper ${TUPLE}-clang-wrapper
echo '#!/bin/bash' > ${TUPLE}-wrapper
echo "exec ${TUPLE}-g\${0:\$[-2]}" "\"\$@\"" >> ${TUPLE}-wrapper
echo '#!/bin/bash' > ${TUPLE}-clang-wrapper
echo "exec ${TUPLE}-\$(basename \${0}) \"\$@\"" >> ${TUPLE}-clang-wrapper
chmod 755 ${TUPLE}-wrapper
chmod 755 ${TUPLE}-clang-wrapper
ln -s ${TUPLE}-wrapper cc
ln -s ${TUPLE}-wrapper c++
ln -s ${TUPLE}-wrapper gcc
ln -s ${TUPLE}-wrapper g++
ln -s ${TUPLE}-wrapper gcc-${GCC_VER}
ln -s ${TUPLE}-wrapper g++-${GCC_VER}
ln -s ${TUPLE}-clang-wrapper clang
ln -s ${TUPLE}-clang-wrapper clang++
ln -s ${TUPLE}-clang-wrapper clang-${CLANG_VER}
ln -s ${TUPLE}-clang-wrapper clang++-${CLANG_VER}
```

Do the following to update the symlinks for distcc and enable automatic symlink update in case of distcc/gcc/clang upgrade:

```bash
/usr/local/sbin/distcc-fix
cat >> /etc/portage/bashrc << EOF
case ${CATEGORY}/${PN} in
    sys-devel/distcc | sys-devel/gcc | sys-devel/clang)
        if [ "${EBUILD_PHASE}" == "postinst" ]; then
            /usr/local/sbin/distcc-fix &
        fi
    ;;
esac
EOF
```

## Setup on the helper machine

Distcc runs in server mode here.  Emerge `sys-devel/distcc`, and setup the cross-compile toolchain as described in [this article]({filename}/Android/building-lxc-ready-kernel.md) if you haven't done it yet.

Enable `distccd` service on the helper box.  Edit `/etc/conf.d/distccd` and add `--allow 192.168.1.0/24` to `DISTCCD_OPTS` to allow your device to send jobs.  You may also want to configure detailed logging to debug, and separate the log file so that it does not pollute the syslog.  The configuration file comes with descriptive comments for reference.

## Verify

Install something via `emerge`.  Observe if there is any improvement in build time.  Observe `distccd` logs on the helper machine to see if any error happens.  More usages can be found in [the wiki page for distcc](https://wiki.gentoo.org/wiki/Distcc#Usage).
