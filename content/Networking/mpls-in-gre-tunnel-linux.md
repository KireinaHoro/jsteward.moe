Title: MPLS in GRE tunnel on Linux with iproute2
Date: 2017-11-15 18:00
Modified: 2018-02-06 20:20
Category: Networking
Tags: networking, gre, mpls, iproute2
Slug: mpls-in-gre-tunnel-linux
Status: published

## Preface

[MPLS](https://en.wikipedia.org/wiki/Multiprotocol_Label_Switching) can be used for prioritizing traffic, which will be used in JSteward Tech's routing policy.
This article works out how to label packets with MPLS and switch according to packets between two host connected by a GRE tunnel.

## Step 1: the GRE tunnel

Let there be two machines: A and B. A has the address `10.128.0.2` and B has the address `10.128.100.2`. The following creates a GRE tunnel between the host.
We'll use the interface name `foo4` on both ends. Execute all the following with root:

On A:

    ip tun a foo4 mode gre remote 10.128.100.2 local 10.128.0.2
    ip addr a 10.199.0.1 dev foo4
    ip link set foo4 up
    ip rou a 10.199.0.0/24 dev foo4

On B:

    ip tun a foo4 mode gre remote 10.128.0.2 local 10.128.100.2
    ip addr a 10.199.0.2 dev foo4
    ip link set foo4 up
    ip rou a 10.199.0.0/24 dev foo4
    
Verify that the hosts can reach each other by pinging the `10.199.0.0/24` addresses.

## Step 2: MPLS encapsulation

To encapsulate packets that go through the GRE tunnel with MPLS header, we have to replace the default route with encapsulation rules, and add corresponding
decapsulation rules on the other end. Label 100 will be used for traffic that goes from A towards B, while label 101 will be used for traffic that goes from
B towards A. Execute all the following with root:

On A:

    sysctl -w net.mpls.platform_labels=65535
    sysctl -w net.mpls.conf.foo4=1
    ip rou c 10.199.0.0/24 encap mpls 100 dev foo4
    ip -f mpls rou a 101 dev lo

On B:

    sysctl -w net.mpls.platform_labels=65535
    sysctl -w net.mpls.conf.foo4=1
    ip rou c 10.199.0.0/24 encap mpls 101 dev foo4
    ip -f mpls rou a 100 dev lo

Packets sent from one peer will be labeled with its corresponding label, and then decapsulated at the other end and delivered to its local interface.

Note that `rp_filter` needs to be set to relaxed mode or completely disabled for packets to be accepted correctly. Do the following on both machines:

    sysctl -w net.ipv4.conf.all.rp_filter=2

Now the both machines should be able to ping each other, and when capturing the packets with `tcpdump`, one will see that the packets have the MPLS header.
