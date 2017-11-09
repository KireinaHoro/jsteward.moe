Title: Proper routing for HE Tunnelbroker on machines with native (and preferred) IPv6 on Gentoo (with `netifrc`)
Date: 2017-11-10 0:00
Modified: 2017-11-10 0:00
Category: Networking
Tags: networking, gentoo
Slug: he-ipv6-routing-on-machines-with-ipv6

## Preface

On a machine with native IPv6 that's working quite well (e.g. CERNET2),
it's usually desirable to set the host's default IPv6 route to go through
native IPv6. Yet the cheap `/48` address block offered by HE Tunnelbroker
can be useful if one wish to assign IPv6 addresses through VPN. This
article mainly serves as a memo for achieving the following goals:

 - native IPv6 should work just fine (i.e. `default` route untouched)
 - tunnelbroker's addresses should work as well (e.g. services that bind to
 the tunnelbroker's addresses should get correct routes)

## The `default` route

For native IPv6, a `default` route would normally look like this:

    default via fe80::c256:27ff:fed2:90fd dev wlp3s0 proto static metric 600 pref medium

... which sets the router's link-local address (acquired via router advertisement)
as the default gateway, thus defining route for all outgoing packets to go through the
physical port.

The problem is, the native IPv6 routers usually filter the packets based on src address ACL.
As a result, the packets with the tunnelbroker's address as the src address usually get dropped
instead of further routed, thus making the tunnel effectively useless.

Linux's iproute2 tool has the `ip-rule` tool, which handles policy routing, and can solve the
problem. What we need is a new `default` route for packets with src addresses that fall in
the prefix allocated from tunnelbroker. The following works like a charm:

    ip -6 route add default dev he-ipv6 table 101
    ip -6 rule add from 2001:470:f838::/48 lookup 101 priority 500

... where `he-ipv6` and the prefix correspond to what you get from HE.

To get things fixed and automatically set up across reboots, we'll need to configure the network
manager to automatically add the RPDB rules as well as the extra routes in the special table `101`.
On Gentoo this is handled via `netifrc`, whose configuration lies in `/etc/conf.d/net`. Things should
look like this:

    rules6_he_ipv6="
    from 2001:470:f838::/48 lookup he priority 500
    "
    routes_he_ipv6="
    ::/0 dev he-ipv6 table he
    "

The `table he` is defined in `/etc/iproute2/rt_tables` as an alias of `table 101` so that we can get
clearer (thus better memorable) rules and routes. Note that `::/0` is used here as I can't find a way
to separate IPv4 and IPv6 routes here (!), and the simple `default` will result in the route got added
into IPv4 routing table.

## One more thing

One thing that bothered me for quite some time is somehow unrelated to routing itself, but worth noting
as failing to notice this will result in strange results. **Make sure your IPv4 firewall permits `ipv6`
packets (a.k.a. protocol 41)!** Like this:

    iptables -A INPUT -p ipv6 -j ACCEPT

I used to have things like this:

    iptables -P INPUT DROP
    iptables -A INPUT -m state --state RELATED,ESTABLISHED -j ACCEPT
    iptables -P OUTPUT ACCEPT

... which results in incoming packets won't reach the destination *unless* the host sends a packet first,
thus triggering the connmark. Inbound connections fail after the tunnel turns inactive for a while, when
the conntrack expires.
