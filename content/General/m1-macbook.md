Title: Apple Silicon Use Report
Date: 2021-08-12 18:00
Modified: 2021-08-12 18:00
Category: General
Tags: apple-silicon, m1, mac, apple
Slug: apple-silicon-use-report
Status: published

It's been over half a year since I accepted the donation of a M1 MacBook Air from [@jiegec](https://t.me/jiegec) and I've been procrastinating for the promised use report.  I finally got some free time to sum up the overall experience and rough edges during daily use, so here we are!  While this post mainly focuses on the experience of the Apple Silicon-equipped version of 2020 MacBook Air, some reviews will probably be more about macOS and Apple itself since this is the first Mac I've extensively used.  Let's get started!

![About this Mac]({static}/images/m1-ueber-diesen-mac.png)

**Note**: this article is written on the M1 MacBook Air using Vim inside iTerm.

**Disclaimer**: I'm in no form affliated with Apple and this is article does not serve as a recommendation or advertisement.  The descriptions merely reflects my personal experience and YOUR MILEAGE MAY VARY.  Having said that, welcome to share your ideas in the comments below.

## Chassis & Build Quality

I'm generally pleased with the design and build quality of the hardware.  As there're plenty of hardware reviews out there, I list a few points in my experience that's worth noting:

- The body is **sturdy** and does not flex, even if held on the edge with one hand; no wobbling or creaky sounds (unlike my 4-year-old ThinkPad)
- The machine is light, but not too light such that it would easily fall off places
- Speaker is really good - **loud but clear**, great spatial audio effects
- Great battery life!  Sustained use under light loads -> 12+ hours of battery life
- Good screen with satisfying peak brightness, color accuracy, and resolution - the aspect ratio (16:10) is especially great
- Personally I do not hate the keyboard with **shallow key travel**, but it can **get quite loud** under heavy use (I daily-drive an HHKB, so hard key presses).  The key caps are large and good
- Port selection (two USB 4 Type-Cs) is a minus but not deal breaker; used to **carrying a hub** after half year's use
- Good microphones for conferencing, but they **do not work** when the **lid is closed**; seems like a [security feature](https://www.reddit.com/r/macbook/comments/fit8wb/is_it_possible_to_enable_the_microphone_when_the/)
- No cooling fans, but has similar thermals with previous Intel Airs (I've used one on intern) - a **quiet** experience, which is very satisfying for my sensitive hearing

One single flaw that's infamous among MacBooks, especially those sold in China, is that the bundled charger does not have a ground pin and the chassis can get tickling or even electrically shock the user when charging.  This is still the case with the M1 MacBook Air, so make sure you [protect your sensitive body parts with sufficient shielding](https://twitter.com/mariotaku/status/496733277274013696).

## Performance - Sustained Loads

The overall performance of the system is very satisfying.  This includes the performance of native applications as well as x86 applications simulated with Rosetta 2 under a wide range of workloads.  I'll share some experiences from daily use that really impressed me.  The sustained load tests are more about native applications and not Rosetta-enabled ones, as most development tools should have Apple Silicon native support after over half a year since release.

### LLVM

The M1 chip has so much better single-core performance that it (Apple Silicon M1, 16GB RAM) has performance on par with a full-blown Intel server (Dual [Intel(R) Xeon(R) Silver 4110 CPU @ 2.10GHz](https://ark.intel.com/content/www/de/de/ark/products/123547/intel-xeon-silver-4110-processor-11m-cache-2-10-ghz.html), 64GB RAM) for a quick LLVM compile test.  The Mac uses internal SSD for storage while the Intel server uses a SATA SSD.  The results are obtained using LLVM monorepo commit `b5f3a128bf8cae46ccf0616477a4775fd168fd7c` with the following CMake options:

```console
$ cmake ../llvm -DCMAKE_BUILD_TYPE=Release -DLLVM_TARGETS_TO_BUILD="AArch64;RISCV;X86" -DLLVM_ENABLE_PROJECTS="clang;compiler-rt;libcxx;libcxxabi;lld" -G Ninja
```

On the Apple Silicon Mac:

```console
[6214/6214] Linking CXX executable bin/lld
ninja  8523,18s user 283,68s system 747% cpu 19:38,01 total
```

On the Intel server:

```console
[5538/5538] Generating ../../bin/llvm-readelf
ninja  34268.50s user 1546.18s system 3084% cpu 19:21.05 total
```

The 4+4 core M1 chip is only ~1.46% slower than the 16C32T Intel server for roughly the same workload!  It's also worth noting that the M1 chip started out very fast but throttled very hard once hitting the 85 degree Celcius temperature wall, when it was about half way (~3500) through the 6214 build targets.

### Scala

This effect can be demonstrated better with a spikey and less scalable workload, such as Scala compiling.  With the [chipsalliance playground](https://github.com/KireinaHoro/chipsalliance-playground), the performance superiority of the M1 chip is more pronounced:

On the Apple Silicon Mac:

```console
[#2] [1132/1132] playground.compile
mill -j 0 _.compile  2,93s user 4,40s system 2% cpu 4:11,39 total
```

On the Intel server:

```console
[#22] [1132/1132] playground.compile
mill -j 0 _.compile  15.94s user 11.09s system 6% cpu 6:56.15 total
```

With a better thermal design (rather than the fan-less design on the Air), even better performance can be expected.

## Application Experience

Most desktop applications that should run on a Mac runs on the M1 Mac.  Native applications usually works without issues.  The translated applications are usually games and desktop applications with GUI that proprietary and less popular, but still most of them works just fine.  As desktop applications do not generally have a raw performance measure available, it is the overall experience that matters.

### Productivity

Generally speaking, very well!  A few things are still translated, but they work just fine.

- Chrome and Safari are of course all native and well-optimized.  macOS supports separate windows for Chrome apps, allowing them to be pinned onto Dock separately with logo, so Google {Calendar,Keep,...} works great and integrated with the system.
- Microsoft Office has always been choppy on Macs, but they work fine thanks to the native builds and thus improved performance.
- Acrobat is still translated and and can stutter when quickly scrolling over complicated PDFs, but the editting works just fine when you focus on a small portion of the document.  The builtin Preview.app is very smooth with good gesture support and can handle most PDF reading.
- Zotero is still translated, but as it's not heavy everything's just fine.
- IM and video conferencing stuff works without issues.
- Mail.app sometimes uses excessive CPU and is usually resolved through relaunching.

### Development

Good experience, but can get confusing in complicated cases due to Rosetta messing with the toolchain.

- Homebrew has native M1 support at the time of writing, so most tools are already rebuilt natively (you can still get a few x86 casks though, but they still work just fine).
- Most IDEs (that I use) now natively support M1, to name a few the JetBrains series, Xcode (of course!), VSCode.  My experience  is now so much better as it can handle much larger projects previously not feasible to use in an IDE (e.g. LLVM in CLion, Chipyard in IntelliJ, etc.) due to index getting too large.
- Toolchains can get a little bit tricky as it is possible to mix up x86 and arm64 libraries, leading to symbol errors during linking.  This can only be fixed in a case-by-case manner and *may lead to significant frustration*.

### Multimedia

Everything works just as on an Intel Mac.

- Video playback is usually smooth with the well-known IINA player.  I sometimes need BluRay menu support, so VLC is a backup that always works.
- Safari's audio system is **at most times broken**.  The audio output is usually stuttering whenever I want to use it, and can be resolved by rebooting once or twice, but this annoys me *a lot*.  I generally avoid Safari for anything related to audio.
- A DSP plugin called [Reference](https://www.sonarworks.com/Reference) is a good example of how drivers can still work after macOS banned third-party kexts.  The application is translated and still works just fine, which wouldn't be possible if it's still using kexts and not the usermode driver framework.

### Steam and games

The few games with macOS support works really good.

- The Steam client browses libraries and store pages smoothly even if under translation.
- Games (the few ones that support macOS) usually run just fine without framerate issues.  Only if more games supported macOS...
- Steam's in-house streaming works great using Moonlight if the latency is low.

### Creativity

I'm not a creator, but using the machine for some light creation is just fine.

- Omnigraffle works just fine through Rosetta.
- Native Premiere Pro (Beta) can easily handle simple projects but quickly hits the ceiling after adding a few transitions and translations.

## Virtualization

The M1 chip, as an ARMv8.4 processor, comes with virtualization support.  This can be utilized by either [QEMU with `hvf` acceleration](https://gist.github.com/citruz/9896cd6fb63288ac95f81716756cb9aa) or Parallels.  Parallels recently gets updated to 17 and improved guest graphical performance such that it is possible to run Windows-only games inside a Windows 10/11 on ARM VM, such as [World of Warships](https://worldofwarships.asia/de/).  Windows on ARM comes with its own x64-to-aarch64 translation, but as the VM can't use the [builtin Intel memory order mode](https://www.infoq.com/news/2020/11/rosetta-2-translation/) available in M1 chip, this suffers a performance penalty.  The machine can get pretty hot and degrade in battery life when using a virtual machine.

## System Scheduling & Swapping

macOS on M1 feels really snappy and responsive even under heavy loads, and this is partly due to the [OS scheduler](https://arstechnica.com/gadgets/2021/05/apples-m1-is-a-fast-cpu-but-m1-macs-feel-even-faster-due-to-qos/) that performs fine-grain QoS towards the big.LITTLE clusters, as well as [eager swapping](https://medium.com/codex/the-apple-m1-ssd-swapgate-is-a-massive-overreaction-50002ee23d0).  Personally, after 9 months of daily driving, my SSD has not experienced the extreme levels of wearing like some early reports:

```
Available Spare:                    100%
Available Spare Threshold:          99%
Percentage Used:                    0%
Data Units Read:                    47,212,581 [24,1 TB]
Data Units Written:                 26,712,479 [13,6 TB]
Host Read Commands:                 647,232,854
Host Write Commands:                279,577,858
```

I believe that daily use, plus the 16GB RAM, results in lower memory pressure (my memory pressure percentage usually stays below 40%).  After all, the M1 is still a mobile platform, and the user shouldn't be putting too much load on it at the risk of device longevity (even so if taking the relatively poor thermals into consideration).

## Miscellenous Issues

There are a few misc issues that does not belong to any specific category of applications, but rather to the system itself.  They mildly affect my daily workflow but are not deal-breakers.  Some of these issues may not be M1-specific but common to all Macs.

- The M1 chip only supports 1 external screen (despite the two USB-C ports)!  It is not possible to use two monitors *natively*, although DisplayLink is a software/hardware solution to add more screens with its downsides.
    - Thus, the machine does not support DisplayPort MST (Multi-Stream Transport).  Multiple monitors in a daisy-chain configuration will be mirrored.
- A 2K (2560x1440), 24inch external screen won't be recognized by macOS as a Retina screen, thus scaling is not possible.  I had to increase the size of the content on that screen manually (e.g. zoom in for Chrome/VSCode, increase font size for IntelliJ).
- HDR settings for external secondary screen are not kept after unplugging.  Setting the external screen as the main display *will* make the HDR settings persist, though.
- Paragon NTFS installs a native kext.  While basic functionalities work, it can get a bit unstable under heavy loads and crash the whole system.

## Closing Remarks

I'm generally pleased with the M1 MacBook Air as a product: it feels finished (not much rough edges), efficient, and performant.  There are definitely areas to improve, such as the need for a 32GB or 64GB model, a better-designed chassis for cooling, etc, but this has been a great start.  Even though I don't use iDevices, I believe I'll probably buy a M2 or M3 device again.  Even for people not purchasing Apple products at all, as competition lowers prices and promotes innovation, it's always a good thing for consumers that Apple challenges on Intel and AMD in the mobile computing market.

Finally, **all the best for Apple Silicon!**
