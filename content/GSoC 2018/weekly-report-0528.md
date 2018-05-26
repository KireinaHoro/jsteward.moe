Title: Gentoo GSoC Weekly Report 05/28
Date: 2018-05-26 15:00
Modified: 2018-05-26 15:00
Category: GSoC 2018
Tags: android, gentoo, gsoc
Slug: weekly-report-0528
Status: published

## Summary

This week was planned as the last week for the first (Preparation) and second (Gaining control of the system) parts in my [GSoC 2018 proposal](https://docs.google.com/document/d/1v3yA4rkex5DGiPmdlXOSse5QZrZAL8QDJFNY2fFAMRY/edit).  I'm pleased to announce that I've successfully hit the target as planned: a video demonstration of the work posted on Twitter can be watched [here](https://twitter.com/KireinaHoro/status/1000328318497902593). 

Reading and following the instructions in the following articles in order would form a complete, detailed tutorial to reproduce the work up to this point:

  * Article written in the week before this week:
    * [Building a Gentoo chroot in Android]({filename}/Gentoo/building-gentoo-chroot-in-android.md)
  * Articles I've written this week:
	* [UART on Nexus 6P]({filename}/GSoC 2018/nexus-6p-uart.md)
	* [Booting Gentoo on Nexus 6P]({filename}/Gentoo/booting-gentoo-on-nexus-6p.md)
	* [Buidling a LXC-ready Android kernel with Gentoo toolchain]({filename}/Android/building-lxc-ready-kernel.md)
	* [Starting Android in LXC]({filename}/Android/starting-android-in-lxc.md)
	
Important repositories (excl. experimental ones that do not mean much) created up to this point (the repository names are clickable):

  * [`android_device_huawei_angler`](https://github.com/KireinaHoro/android_device_huawei_angler): holds patch to disable the forced Full-Disk Encryption (as described in the "What's Next?" section in [this article]({filename}/Android/analysis-of-android-cryptfs.md));
  * [`preinit_angler`](https://github.com/KireinaHoro/preinit_angler): holds the `preinit`, initramfs structure, and Makefile rules to easily unpack and repack Android `boot.img`;
  * [`android-lxc-files`](https://github.com/KireinaHoro/android-lxc-files): holds patches, LXC config, startup and stop hooks, and helper scripts for the proper functioning of Android in LXC;
  * [`android_kernel_huawei_angler`](https://github.com/KireinaHoro/android_kernel_huawei_angler): holds the modified version of Android kernel source along with config tweaks to build a LXC-ready kernel with Gentoo cross-compile toolchain.
  
The above repositories still lack proper `README`s, and I put that as the main task for part 4 (Cleaning up) in my GSoC project, whose main goal is to create proper documentation for future pickup.
  
We still lack some sort of distribution / release method, but I think that belongs to the goals in the third part of the project (Taking Android apart), as we'll have stage3 tarballs and automatic setup scripts available directly at the end of that part of work.

We need to modify Android framework to enable it to inform the host about its states.  We also need some sort of interface (e.g. an app) in the Android world to perform actions outside the container (e.g. initialize system updates, switch LXC profiles, etc.) as we proceed further in part 3 of this project.  Some other goals yet to achieve are recorded in the "Known Problems" section in _[Starting Android in LXC]({filename}/Android/starting-android-in-lxc.md)_.

## Plans for the coming weeks

June is drawing near, and it's time for my final-term examinations in the university.  Just as planned in the time schedule, I'll pause all activities of GSoC during June, except filling the form for First Evaluation at around June 15, and restoring to full work capacity at the end of June.  Looking forward to the third part (Taking Android apart) of the project.  Thanks for everyone that devoted time to help me through the second part of the project--it was very fun and I learned a lot in the process.

Happy hacking!
