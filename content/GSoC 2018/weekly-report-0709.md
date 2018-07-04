Title: Gentoo GSoC Weekly Report 07/09
Date: 2018-07-08 0:00
Modified: 2018-07-08 0:00
Category: GSoC 2018
Tags: android, gentoo, gsoc
Slug: weekly-report-0709

## Summary

This is my first week back on GSoC from the final exams, and, according to the proposal, the second part of the project should get started in this week.  This week's work sums up into the following two articles:

  * [Integrating Android kernel source into Portage]({filename}/Gentoo/android-kernel-source-portage.md)
	Introduces how the three components, `preinit`, `installkernel`, and `${BOARD_NAME}-sources` works together to provide a kernel source package that enables users to build and install kernels just like normal Gentoo Linux systems on a Portage-powered Android system.
  * [Brief introduction to the (post-8.0) Android Build System]({filename}/Android/android-build-system.md)
    Summarizes the information I collected via searching and reading sources in AOSP about the current Android build system that came into action at present (Android 8.0 and later).  Attempts to dissect the build system also included.
	
And, as Part I (as the fundamentals for Portage-powered Android) is now (almost) finished (what's left would be to package LXC-related and OpenRC-related things up as a package), I believe that it's time to announce the official short-and-sweet name for the Portage-powered Android project: **SharkBait**!  Despite I'm the person that does most of the coding work (at least during the GSoC session), SharkBait actually has a team under the hood, and they're extremely helpful whenever I get stuck, and provide excellent ideas.  A site is available [here](https://www.shark-bait.org), and despite not much is there at present, it'll definitely grow with time.  We'll have a logo soon as well, so stay tuned!
