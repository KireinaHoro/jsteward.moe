Title: Starting Android in LXC
Date: 2018-05-26 01:00
Modified: 2018-05-26 01:00
Category: Android
Tags: android, lxc, gsoc, gentoo
Slug: starting-android-in-lxc

## Preface

After successfully booting Gentoo [in the previous article]({filename}/Gentoo/booting-gentoo-on-nexus-6p.md), we can move on to launching Android in LXC, which is the last mission in the first period of my GSoC 2018 project.  This article documents the process to bring up Android successfully with most of its functions working; only a few things don't work by now, and they're recorded in the Known Problems section at the end of this article.  Note that while this article strives to provide easy-to-follow instructions, it may not be suitable as a step-by-step tutorial. That is to say, you may encounter problems due to mistakes or things that the author didn't notice.  The author appreciates your understanding when such thing happens; meanwhile, feel free to contact the author by the means listed in the page linked at the bottom of this page.

## Set Up Filesystem for Android

TODO: Stub

## Known Problems

The (non-exhaustive) list of problems as of 2018-05-26:

  * Reboot function in Android system (along with Advanced Reboot) doesn't work.  This is because Android system doesn't actually poweroff the system or reboot it when inside a container: it simply `exit(0)`, making it impossible for the GNU/Linux world (at least for now) to tell how the container stopped.  The current behavior is that the system will power down regardless of whether "Poweroff" or "Reboot" (or other reboot options, e.g. Reboot to bootloader) has been selected in Android.
    * `charger` suffers from similar problems, though a workaround works pretty well; see The Charger section above.
	* This may be fixed by patching Android framework so that it signals the host about how it ended, by placing a file in the `/run` filesystem bind-mounted from the host.  The host then decides whether to reboot or to poweroff according to the signal file.  This is exactly how `charger`'s problem gets fixed.
  * Boot is unbearably slow.  Charging while powered off takes a long time to show the charging animation as well.
    * This is because the _Linux kernel's initialization time_ is long.  It takes over 10 seconds for the kernel to launch the first userspace program--`preinit`.
	* For better experience, the kernel should have most of its functions as kernel modules, so that we can display a boot animation (or a static picture other than the Google logo from bootloader) as early as possible.  We may draw an animation that's unrelated to `bootanim` in Android though.
  * Full-disk encryption / file-based encryption doesn't work.
	* This was done deliberately, as Android's `cryptfs` implementation is a little bit too complicated to implement (see [my previous analysis on Android cryptfs]({filename}analysis-of-android-cryptfs.md)).
	* Standard encryption means should get implemented at some point (e.g. LUKS).
	* Choosing to encrypt device in System Settings in Android can cause __unexpected behaviors__.  _YOU HAVE BEEN WARNED._
