Title: UART on Nexus 6P
Date: 2018-05-22 13:00
Modified: 2018-05-22 13:00
Category: GSoC 2018
Tags: hardware, gsoc
Slug: nexus-6p-uart
Status: published

## The story

As described [here](https://android.googlesource.com/device/google/debugcable), Google baked a serial console into the headphone jack of their Nexus and Pixel devices.  A serial console would be feasible for debugging problems with `init` as well as tinkering the device when it has booted into Linux and haven't started Android yet.  My journey to successfully build such a cable turned out to be quite complicated, though.

## PL2303

PL2303 is a chip that provides 5v and 3v3 TTL tx/rx, which serves as a serial port to communicate with the phone over UART.  @imi415 on Telegram made a cable with circuits to adjust the voltages to match what the phone accepts (1.8v); however, it's not working properly: the bootloader log reads just fine, yet the kernel message won't get to the computer.

After visiting @imi415's lab and having the output voltages from the phone measured, we discovered that the bootloader made output at 2.5v, while the kernel made output at 1.9v.  As PL2303 can't properly handle 1.8v rx, this resulted in the computer not receiving anything at all after kernel starts.

## FT232R

@imi415 suggested that I should try FT232, as it supported 1.8v input; and [this post](http://people.redhat.com/jmcnicol/nexus_debug/) showed that chips from FTDI at 3.3v mode should work fine on Nexus 5X.  As Nexus 5X shouldn't be different from Nexus 6P too much, I purchased a FT232RL TTL board and soldered the headphone cable to some jump wires, and connected them to the FT232RL unit.  Plugging the unit into the computer and firing up PuTTY proved that things worked perfectly.  Credit for the solder work goes to @Catofes on Telegram.

## Pictures

FT232RL TTL Board:

![FT232RL TTL Board]({static}/images/ft232rl.jpg)

FT232RL with voltage converter (but didn't work :/):

![FT232RL with voltage converter (but didn't work :/)]({static}/images/ft232rl-with-voltage-converter.jpg)

Bypassing the voltage converter:

![Bypassing the voltage converter]({static}/images/bypassing-voltage-converter.jpg)

Before soldering the wires:

![Before soldering the wires]({static}/images/before-soldering-wires-together.jpg)

Final product:

![Final product]({static}/images/final-product.jpg)

Console output!

![Console output!]({static}/images/console-output.jpg)
