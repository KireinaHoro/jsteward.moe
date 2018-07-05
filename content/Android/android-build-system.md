Title: Brief introduction to the (post-8.0) Android Build System 
Date: 2018-07-05 04:00
Modified: 2018-07-05 04:00 
Category: Android
Tags: android, gsoc
Slug: android-build-system
Status: published

## Preface

As the main target of the second period of my GSoC 2018 project, I have to take down Android build system and accomodating it into Portage, forming a modular building and updating mechanism.  So, inevitably, I'll have to deal with the original AOSP build system (Lineage OS's is a little bit different, but the core hasn't changed).  In this article, I'll document the information I obtained from the Internet and (a tiny portion of) AOSP source about the build system.  I'll then propose possible solutions to take AOSP apart.

## Present Android build system -- `Android.bp`

If one look at the repository structure of AOSP, he will find many components structured as separate repositories, which together form the AOSP tree.  Inside each repository, code falls into smaller structures called "modules", with each module as a fundamental unit in dependency management and building the process (yeah, it's a complicated system).

Each module has its own build configuration file: `Android.mk` and/or `Android.bp`.
  * `Android.mk` is the good, old format used everywhere by Android, from system components to application packages; it gets parsed into [Ninja](https://ninja-build.org/) files by the [Kati](https://github.com/google/kati) project.
  * `Android.bp` is the new format that gets parsed by [Blueprint](https://github.com/google/blueprint/), and then converted to [Ninja](https://ninja-build.org/) files though detailed build logics defined by [Soong](https://android.googlesource.com/platform/build/soong/). (Actually in AOSP, Blueprint is a part of Soong.)

Developers start building by sourcing the `build/envsetup.sh` script, which sets up necessary environemntal variables as well as some useful functions:

  * `breakfast`: specifies the product to build for.
  * `lunch`: start a full build for the previously picked product.
  * `brunch`: (as its name suggests) the combined effect of `breakfast` and `lunch`.
  * `m`: makes from the top of the tree.
  * `mm`: builds all of the modules in the current directory.
  * `mmm`: builds all of the modules in the supplied directories.
  * `croot`: go back to the root of source tree.

The output will be stored at `out/target/product/${DEVICE}/`, while this path will be stored in the environmental variable `$OUT`.

## Experiments with the build system

AOSP builds are [reproducible](https://reproducible-builds.org/): that is to say, as long as the source doesn't change, the produced binaries are identical.  This was verified by comparing the hash of components already installed on my Nexus 6P with the ones I compile again from the source.  With that, there turns out to be two approaches possible to achieve the goal of breaking Android apart:

  * Parse the `Android.mk` and `Android.bp` files, resolving the relationship between components, and build the components with Portage
    * current problem: despite that `Android.bp` files are simple, the build rules are unclear (Soong had very little documentation and is prone to change *at any time*); `Android.mk` files, on the other hand, can be very complicated: they're full-blown GNU Makefiles.
  * Leave Android build system untouched (mostly) and produce executables by building modules *in* the build system.  We then pack up each of the modules' outputs, removing dependencies from the output, and generating binary packages.
	* current problem: the exact dependency relationship will be difficult, if possible, to find out.
	
It's difficult to say that which route will be picked, and I hope that this week's discussion should shed some light on this somehow tough problem.
