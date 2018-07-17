Title: Using Yubikey as a login token
Date: 2018-07-18 15:00
Modified: 2018-07-18 15:00
Category: Gentoo
Tags: gentoo, yubikey
Slug: yubikey-as-login-token
Status: published

## The story

It has been a while since [I got my Yubikey from Harry Chen]({filename}/General/meet-yubikey.md).  Now that I'm back working on Gentoo, so it is time to explore functions of the Yubikey on Linux.  Instead of just using the Yubikey as a OpenPGP card, its [U2F](https://en.wikipedia.org/wiki/Universal_2nd_Factor) function can serve more than simply logging you into Google.  In this article, we'll show how to make the Yubikey a convenient and secure login token for Linux systems, enabling you to log into the system with a plug and a touch, and lock the session when the token is removed.

## U2F capability for PAM

U2F can be used locally on Linux systems thanks to the [`pam_u2f` module by Yubico](https://github.com/Yubico/pam-u2f).  Emerge `sys-auth/pam_u2f` and add the active user (`jsteward` in my case) to the `usb` group for access to the device:

```bash
emerge -av sys-auth/pam_u2f
gpasswd -a jsteward usb
```

**Note:** remember to log out and then log back in to make the new group settings come into place.

### Register the device

Make sure you've configured the appropriate kernel options (`CONFIG_HIDRAW` and `CONFIG_USB_HIDDEV`).  Plug in the device and observe `dmesg` to see if the deivce is detected by the kernel correctly.  We can then setup the authorization mappings, registers the device to the user that uses it.

```bash
mkdir -p ~/.config/Yubico
pamu2fcfg -ujsteward > ~/.config/Yubico/u2f_keys
```

Touch the device as the LED on it starts blinking.  Verify that the device is properly registered by verifying the contents of `~/.config/Yubico/u2f_keys`.  To use multiple keys, register the device with different authorization file locations (i.e. `u2f_keys`) and then merge them into a single `u2f_keys` in the following format:

    jsteward:<KeyHandle1>,<UserKey1>:<KeyHandle2>,<UserKey2>:...

### Configure PAM module

We want to use our Yubikey for system authentications, which would include logins (DE or tty), session unlock (screensaver), `sudo`, and more.  Place the following line in `/etc/pam.d/system-auth`:

    auth        sufficient  pam_u2f.so cue

Just above the following existing line in the file:

    auth        required    pam_unix.so try_first_pass likeauth nullok

**Note:** the `cue` parameter makes the module display a prompt "Please touch the device." when it is waiting for a response so that the user does not mistake it as the system has hung.

This enables you to authenticate with a Yubikey without the need of user passwords.  To use the Yubikey as a 2FA tool, change `sufficient` to `required`.  However, this will result in failed authentication when the Yubikey is not present (and touched in time).

**Warning:** `system-auth` affects all authentications, including remote ones.  Think twice before using `required` for `pam_u2f` on a server.

**Warning:** messing up PAM configuration may result in being locked out of the system, which is only possible to fix with a LiveCD or `init=/bin/bash`.

Test the configuration by trying to log in or sudo.  SDDM logins will be a little bit tricky due to the way it is designed: press Login without entering a correct password and touch the device.

## Lock the session when Yubikey gets removed

This works with a simple `udev` rule.  For an easy way of locking sessions, use `elogind` instead of the default `consolekit` (on Gentoo) as described in the [Gentoo Wiki page for `elogind`](https://wiki.gentoo.org/wiki/Elogind).  Write the following rule in `/etc/udev/rules.d/20-yubikey.rules`:

    ACTION=="remove", ENV{ID_BUS}=="usb", ENV{ID_MODEL_ID}=="0407", ENV{ID_VENDOR_ID}=="1050", RUN+="/bin/loginctl lock-sessions"

Check your Yubikey's VID:PID pair and substitute `1050:0407` accordingly.  Reload the udev rules:

    sudo udevadm control --reload-rules

Unplug your Yubikey to see the rule in action.
