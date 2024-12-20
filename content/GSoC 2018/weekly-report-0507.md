Title: Gentoo GSoC Weekly Report 05/07
Date: 2018-05-04 11:00
Modified: 2018-05-04 11:00
Category: GSoC 2018
Tags: android, gentoo, gsoc, linux
Slug: weekly-report-0507
Status: published

## Preface

This week was about getting the Gentoo stage3 to work on Android (as a subsystem of Android currently), and replacing init located in the initramfs, which was part of the `boot.img` that was used to boot the system. To ease the process of compiling for a different architecture, I installed a Gentoo guest in Hyper-V on my laptop and built a cross-compile toolchain for `aarch64-unknown-linux-gnu` in it. As the three things does not relate to each other very much, I'm splitting them into three separate articles, and placing the link below for reference.

  * [Building a Gentoo chroot in Android][1]
  * [Installing Gentoo in Hyper-V][2]
  * [Replace Android init with test script][3]
  
[1]: {filename}/SysAdmin/building-gentoo-chroot-in-android.md
[2]: {filename}/SysAdmin/install-gentoo-in-hyper-v.md
[3]: {filename}replace-android-init-with-test-script.md
