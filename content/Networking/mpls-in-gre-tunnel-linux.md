Title: MPLS in GRE tunnel on Linux with iproute2
Date: 2017-11-15 18:00
Modified: 2018-05-16 0:00
Category: Networking
Tags: networking, gre, mpls, iproute2
Slug: mpls-in-gre-tunnel-linux
Status: published

## Preface

[MPLS](https://en.wikipedia.org/wiki/Multiprotocol_Label_Switching) can be used for prioritizing traffic, which will be used in JSteward Tech's routing policy.
This article works out how to label packets with MPLS and switch according to packets between two host connected by a GRE tunnel.

## Before you start

Full MPLS support wasn't present in Linux kernel until lately (4.3 at least), so check your kernel version before trying out things in this article; incompatiable kernels will most likely give out the following two types of errors:

	# ip -f mpls route add 101 dev lo
	RTNETLINK answers: Operation not supported
	
... which says by itself pretty much. Another type of error looks like this:

	# sysctl -w net.mpls.conf.foo4.input=1
	sysctl: cannot stat /proc/sys/net/mpls/conf/foo4/input: No such file or directory
	
This means that you haven't loaded the correct kernel modules (`mpls_router` in this case). Userspace tools should get the modules loaded on demand, though; the (most likely non-exhaustive) list for MPLS-related kernel modules are as follows:

  * mpls_router
  * mpls_gso
  * mpls_iptunnel

Make sure that you have the suitable kernel as well as the correct set of kernel modules--maybe your Enterprise Linux vendor has back-ported things to older kernels, but I wouldn't be able to help in those cases: contact your vendor for support as you pay them for that. If you use Gentoo (and don't use `genkernel all`, which is evil), try enabling everything related to MPLS to avoid cryptic errors. To tell if your kernel really supports MPLS, issue the following, and you should see output like this for __all__ of your interfaces:

	# sysctl -a --pattern mpls
	net.mpls.conf.eth0.input = 0
	net.mpls.conf.eth1.input = 0
	net.mpls.conf.lo.input = 0
	net.mpls.platform_labels = 0

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
    sysctl -w net.mpls.conf.foo4.input=1
    ip rou c 10.199.0.0/24 encap mpls 100 dev foo4
    ip -f mpls rou a 101 dev lo

On B:

    sysctl -w net.mpls.platform_labels=65535
    sysctl -w net.mpls.conf.foo4.input=1
    ip rou c 10.199.0.0/24 encap mpls 101 dev foo4
    ip -f mpls rou a 100 dev lo

Packets sent from one peer will be labeled with its corresponding label, and then decapsulated at the other end and delivered to its local interface.

Note that `rp_filter` needs to be set to relaxed mode or completely disabled for packets to be accepted correctly. Do the following on both machines:

    sysctl -w net.ipv4.conf.all.rp_filter=2

Now the both machines should be able to ping each other, and when capturing the packets with `tcpdump`, one will see that the packets have the MPLS header.
