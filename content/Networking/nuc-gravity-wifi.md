Title: Gravity Access Wi-Fi on NUC VM
Date: 2021-02-15 22:00
Modified: 2021-02-15 22:00
Category: Networking
Tags: networking
Slug: nuc-gravity-wifi
Status: published

## Preface

Winter vacation means that most of my time is spent at home, instead of the dorm room.  The consequence of this is that those dumb devices that require access to _Gravity_ to properly function is now basically offline, as they're not capable of dialing in via IKEv2 or WireGuard for remote access by themselves.  These are some examples of such devices (and where they're trying to communicate with):

- Kindle (_amazon.co.jp_)
- Chromebooks (_google.com_)
  - Note that while Chromebooks, when set up, are capable of dialing a VPN, they are not in the _Welcome_ screen
- Android phones (_google.com_)
  - Same as above
  
With the help of a NUC borrowed from [@Catofes](https://t.me/Catofes), we can set up a WiFi access point to _Gravity_ for these devices.  While it is true that the performance is going to be somewhat limited, we're not doing much other than syncing e-books, looking up Wikipedia definitions, and signing into Google accounts, so that should suffice.  Here's a list of what we're going to set up:

- __Platform__: VM, WiFi card passthrough, OS
- __Backhaul__: Gravity address allocation, WireGuard site-to-site
- __Access__: 802.11 - Hostapd, ISC DHCP - DHCP & DHCPv6, RADVD - SLAAC
- Profit!

Let's get started!

## The platform

The NUC itself runs ESXi 7.0 to support some other tasks (mainly IoT stuff) that are not covered in this article.  We're using a Debian 10 VM with the Intel 7265D WiFi card passthrough.  A single core and 256 MB of RAM is enough to run the site-to-site VPN, hostapd, and all the address handout stuff.

A quick check with `iw list` shows that the 7265D is recognized and passthrough correctly, that it supports AP mode, but only in 2.4GHz:

```text
Wiphy phy0
...
        Supported interface modes:
                 * IBSS
                 * managed
                 * AP
                 * AP/VLAN
                 * monitor
                 * P2P-client
                 * P2P-GO
                 * P2P-device
...
        Band 1:
...
                Frequencies:
                        * 2412 MHz [1] (22.0 dBm)
                        * 2417 MHz [2] (22.0 dBm)
                        * 2422 MHz [3] (22.0 dBm)
                        * 2427 MHz [4] (22.0 dBm)
                        * 2432 MHz [5] (22.0 dBm)
                        * 2437 MHz [6] (22.0 dBm)
                        * 2442 MHz [7] (22.0 dBm)
                        * 2447 MHz [8] (22.0 dBm)
                        * 2452 MHz [9] (22.0 dBm)
                        * 2457 MHz [10] (22.0 dBm)
                        * 2462 MHz [11] (22.0 dBm)
                        * 2467 MHz [12] (22.0 dBm) (no IR)
                        * 2472 MHz [13] (22.0 dBm) (no IR)
                        * 2484 MHz [14] (disabled)
...
        Band 2:
...
                Frequencies:
                        * 5180 MHz [36] (22.0 dBm) (no IR)
                        * 5200 MHz [40] (22.0 dBm) (no IR)
                        * 5220 MHz [44] (22.0 dBm) (no IR)
                        * 5240 MHz [48] (22.0 dBm) (no IR)
                        * 5260 MHz [52] (22.0 dBm) (no IR, radar detection)
                        * 5280 MHz [56] (22.0 dBm) (no IR, radar detection)
                        * 5300 MHz [60] (22.0 dBm) (no IR, radar detection)
                        * 5320 MHz [64] (22.0 dBm) (no IR, radar detection)
                        * 5500 MHz [100] (22.0 dBm) (no IR, radar detection)
                        * 5520 MHz [104] (22.0 dBm) (no IR, radar detection)
                        * 5540 MHz [108] (22.0 dBm) (no IR, radar detection)
                        * 5560 MHz [112] (22.0 dBm) (no IR, radar detection)
                        * 5580 MHz [116] (22.0 dBm) (no IR, radar detection)
                        * 5600 MHz [120] (22.0 dBm) (no IR, radar detection)
                        * 5620 MHz [124] (22.0 dBm) (no IR, radar detection)
                        * 5640 MHz [128] (22.0 dBm) (no IR, radar detection)
                        * 5660 MHz [132] (22.0 dBm) (no IR, radar detection)
                        * 5680 MHz [136] (22.0 dBm) (no IR, radar detection)
                        * 5700 MHz [140] (22.0 dBm) (no IR, radar detection)
                        * 5720 MHz [144] (22.0 dBm) (no IR, radar detection)
                        * 5745 MHz [149] (22.0 dBm) (no IR)
                        * 5765 MHz [153] (22.0 dBm) (no IR)
                        * 5785 MHz [157] (22.0 dBm) (no IR)
                        * 5805 MHz [161] (22.0 dBm) (no IR)
                        * 5825 MHz [165] (22.0 dBm) (no IR)
...
```

Note how every frequency in the 5GHz band is marked with __no IR__, which means no _initiating radiation_ [apparently](https://www.spinics.net/lists/linux-wireless/msg124066.html).  While this is most likely a regulatory limitation, soft or hard, I don't feel bothered to bypass this.  We're sticking with 2.4GHz for now.

## The backhaul

Backhaul in the current situation means bridging the incoming devices into _Gravity_.  While it is possible to run a full node on the NUC VM, I don't really feel the need to do so: we're behind multiple layers of NAT (3 layers if including the ISP's), no good IPv6, and not stable enough to relay traffic for the rest of the network.  Instead, a site-to-site VPN through WireGuard to a full node will serve the purpose.  Note that this is very similar to the _Gravity_ AP deployed at my dorm, which uses GRE for its lightweight and sharing the campus network with the full node.  WireGuard should help with traversing NATs this time.

Note that no address is assigned to the WireGuard interface on the NUC VM; the gateway address sits on the wlan adapter.  WireGuard works just fine forwarding these packets with the `fwmark`-based default route handling (from [`wg-quick`](https://manpages.debian.org/testing/wireguard-tools/wg-quick.8.en.html)).

### _Gravity_ address allocation

As we're planning full dual-stack access, the following two blocks are alloted to this new site:

- IPv4: `10.172.194.128/25` (private)
- IPv6: `<prefix redacted>:cc20::/60`

The first host address of each network is the gateway and sits on the new site.  These should not collide with anything else currently...

## The AP

### hostapd - L2

Hostapd runs the AP in 802.11n mode.  The configuration is pasted below for future reference.

```text
# /etc/hostapd/hostapd.wls192.conf
interface=wls192
hw_mode=g
channel=10
ieee80211d=1
country_code=CN
ieee80211n=1
wmm_enabled=1

ssid=JSteward Access
auth_algs=1
wpa=2
wpa_key_mgmt=WPA-PSK
rsn_pairwise=CCMP
wpa_passphrase=<redacted>
```

We also need to edit `/etc/hostapd/ifupdown.sh` to activate the `run-parts` hook of `ifupdown` to start and stop `hostapd` automatically.  Insert this at the beginning:

```bash
if [ -f /etc/hostapd/hostapd.${IFACE}.conf ]; then
        IF_HOSTAPD="/etc/hostapd/hostapd.${IFACE}.conf"
fi
```

### ifupdown - L3

As stated in the previous section, the gateway address sits on the wlan interface (for ARP/RA).  The configuration is pasted below for future reference.

```text
# /etc/network/interfaces
# Ethernet/lo configuration elided
# wifi AP
auto wls192
iface wls192 inet static
        pre-up systemctl start --no-block wg-quick@seki
        address 10.172.194.129/25
        post-down systemctl stop --no-block wg-quick@seki

iface wls192 inet6 static
        dad-attempts 0
        address <prefix redacted>:cc20::1/60
```

Note the `--no-block` option to `systemctl`; this is necessary, otherwise the attempt to `ifup -a` at boot time will timeout due to name resolution issues (the Ethernet connection is not up yet).  Having it delay a little bit solves all the problems.

### ISC DHCP & RADVD - address distribution

`radvd` and `isc-dhcp-server` works together to automatically hand out addresses to clients dual-stack.  DHCPv4 is relatively simple:

```text
# /etc/dhcp/dhcpd.conf
option domain-name "jsteward.moe";
option domain-name-servers 8.8.8.8, 8.8.4.4;
default-lease-time 600;
max-lease-time 7200;
ddns-update-style none;

subnet 10.172.194.128 netmask 255.255.255.128 {
  range 10.172.194.130 10.172.194.254;
  option routers 10.172.194.129;
}
```

DHCPv6 is just as simple.  Note that there's no `routers` option for DHCPv6 though; the gateway (usually as an LL address) needs to be handed out though router advertisement.  For consistency, DNS name server and search domain will be handed out via router advertisement as well.

```text
# /etc/dhcp/dhcpd6.conf
default-lease-time 2592000;
preferred-lifetime 604800;
option dhcp-renewal-time 3600;
option dhcp-rebinding-time 7200;
allow leasequery;
option dhcp6.info-refresh-time 21600;

subnet6 <prefix redacted>:cc20::/60 {
        range6 <prefix redacted>:cc20:b::1 <prefix redacted>:cc20:b::ff:ffff;
}
```

RADVD here works in the [so-called](https://docs.opnsense.org/manual/radvd.html) _Assisted_ mode:

> Assisted: Stateful configuration, address configuration provided by DHCPv6, although advertised routes can also be used on Stateless Address Autoconfiguration setups (SLAAC).

```
# /etc/radvd.conf
interface wls192 {
        AdvSendAdvert on;
        AdvManagedFlag on;
        AdvOtherConfigFlag on;
        MinRtrAdvInterval 3;
        MaxRtrAdvInterval 10;
        prefix <prefix redacted>:cc20::/60 {
                AdvOnLink on;
                AdvAutonomous off;
        };
        prefix <prefix redacted>:cc2a::/64 {
                AdvOnLink on;
                AdvAutonomous on;
        };

        RDNSS 2001:4860:4860::8888 2001:4860:4860::8844 { };
        DNSSL jsteward.moe { };
};
```

The SLAAC block (`<prefix redacted>:cc2a::/64`) uses a different prefix for easy distinguishing.  Note that for unknown reasons using just one single `AdvAutonomous` `/60` prefix for both SLAAC and DHCPv6 didn't work; please leave a comment below if you have any clues.

## Results

The system can support about 50Mbps downlink and 20Mbps uplink with an 2020 Macbook Air, translating to about 15% utility (all kernel time) on a single core.  Considering that we're running this on 2.4GHz band, the bottleneck is most likely due to 7265D's Tx power limits and/or bad channel selection.  In addition, the coverage is pretty bad as well, with signals barely usable outside the bedroom (the NUC is placed on the desk with plenty of cords on top).  But, just as described in the preface, this should be sufficient for most of the use cases.  Happy hacking!
