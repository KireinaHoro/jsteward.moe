Title: JSteward Tech Internal Network Design
Date: 2017-11-11 15:00
Modified: 2017-11-11 15:00
Category: Networking
tags: networking, infrastructure
Slug: jsteward-tech-internal-network-design
Status: published

## Preface

As the number of machines I manage increase gradually, it has become a necessity to connect the machines
together through secure, reliable tunnels, thus forming an internal network. A private network can have the following
advantages:

 - Ease of configuring services that involve multiple machines, such as a databases and database clients
 - Data inside the network are controlled, thus eliminating the need of unnecessary application layer
security
 - Convenience when configuring optimal route for network clients that wish their traffic be sent through the network

This article mainly describes the structure of the network (i.e. how the sites are connected), address allocation and
route selection. It should serve as the document to how the network should be implemented afterwards, though further
revisions may take place.

## Part one: how are machines interconnected

A node in the network shall have one and only one of the following roles:

 - a server (a.k.a. a *core router*)
 - a client (a.k.a. an *end user*)
 - a small router

A **server** connects to other servers, forming a full mesh network between the servers. A **small router** behaves just
like a server, except that it only connects to **one** server, instead of *every* server (that's what *full mesh* means).

A **client** connects to the network via one of the following:

 - a **server** (through *remote access*: using a normal VPN protocol)
 - a **small router** (through normal IP)

The following sections define the detailed properties of possible connections between the networks.

### **Server** to **server** and **small router** to **server**

The two hosts should connect to each other through GRE over IPsec. The IPsec tunnel should be managed by `strongswan`.
Both ends should authenticate each other through X.509 certificates, issued by the PKI managed by JSteward Tech.

### **Client** to **server**

The client should establish a VPN session to the server, with one of the following protocols:

 - IKEv2
 - IPsec Hybrid RSA

### **Client** to **small router**

The client should connect to the small router directly via physical media, such as an ethernet cable or a WiFi connection.

## Part two: how are addresses allocated

JSteward Tech does not process any IP's for now, neither IPv4 nor IPv6. For IPv4 and IPv6 the policy for assigning addresses
are a little different. They're described in detail in the sections below.

### IPv4

Judging from the current situations, it's not possible in the near future for JSteward Tech to acquire public IPv4 prefixes,
thus the private network `10.192.0.0/10` is used. All addresses will be assigned inside this network.

For each server, including small routers, a `/16` in the network will be assigned to it, in a continuous manner, that is, the
prefixes are assigned to each server *one-by-one*.

All clients that connect to a server, including small routers, will get their address from the first `/17` in the server's `/16`
network. The second `/17` is reserved for the server's own applications (such as containers).

### IPv6

Currently, JSteward Tech doesn't possess public IPv6 addresses. Yet many of the servers, including small routers, have native
IPv6 (provided by CERNET2 or VPS provider). Such addresses are obtained via router advertisement with prefix `/64`.

For small routers without native IPv6, it should receive a `/80` from its upstream (i.e. the server it connects to). For servers
whose prefix is not routable (thus impossible to use `ndppd` to further split the network) or without native IPv6, it should get
its `/64` from HE tunnel broker, which should be connected to one of the servers.

All clients get a `/96` from its upstream, regardless of it being a small router or a server. This should be achieved through
`ndppd`, in order to get the correct routes, as prefixes longer than `/64` will break SLAAC.

If JSteward Tech should possess any public IP addresses, they should be assigned to servers without native IPv6, replacing what
HE tunnelbroker does for now. Due to this possibility, the IPv6 address assignment section is prone to changes.

## Part three: how are routes selected

Note: IPv6 routes are not discussed here. All IPv6 data should simply follow its upstream's native IPv6 rules and go out into the public
Internet wherever possible.

The IPv4 traffic that goes through this network fall into *exactly* one of the following categories:

 - it goes to a host **inside** the network (e.g. a server in the network that serves contents)
 - it goes to a host **outside** the network (e.g. when a client uses the network as some kind of proxy)

The following sections discuss the two kinds of network traffic in detail.

### To a host **inside** the network

JSteward Tech will use iBGP for route exchanging within the network. Route selection will be based on link latency and bandwidth,
with latency as the first consideration. This will be achieved through dynamically alternating the `bgp_community` values, whose data
is acquired through a live monitoring system. The following documents should help when implementing the system, thus listed here for
future reference:

 - [DN42's Bird howto](https://dn42.eu/howto/Bird)
 - [DN42's Bird BGP community howto](https://dn42.eu/howto/Bird-communities)
 - [Bird documentation](http://bird.network.cz/?get_doc&f=bird-6.html#ss6.3)
 - [Example on monitoring a network and visualizing data with Grafana](https://lkhill.com/using-influxdb-grafana-to-display-network-statistics/)

### To a host **outside** the network

MPLS shall be utilized to identify the exit preferred when a data packet enters the core, in which the exit is selected according to
a predefined table describing which exit a packet should choose based on its destination address. The packet is then encapsulated with
the appropriate MPLS label according to the exit chosen, and routed through the core. Actions in the [LSP](https://en.wikipedia.org/wiki/Multiprotocol_Label_Switching#Label-switched_path)
are defined as follows:

 - a LER (label edge router) encapsulates the packet with MPLS label selected by destination address and sends it to the next hop determined
by the optimal next hop to the egress router according to the iBGP routing table
 - a LSR (label switching router) swaps the the label with one identical to the original one (i.e. leave the label *untouched*) and sends it
to the next hop determined by optimal next hop to the egress router according to the iBGP routing table
 - the egress router decapsulates the MPLS label, does MASQUERADE and sends the packet out into the Internet.

Due to the nature of needing to operate on the MPLS table every time the link latency changes (and that the iBGP routing table changes), a
helper program will be needed to update the MPLS routes every time such change occurs.

For a host that wishes to select the exit node of its traffic on its own instead of conforming to the predefined table at the LER, the server
can act as an LER itself, encapsulating the packets with the desired label corresponding to the exit chosen. Then the packets will be routed to
the desired exit by the LSR's on the LSP.

The following documents should help when implementing the system, thus listed here for future reference:

 - [MPLS over GRE experiment on my own blog](/mpls-in-gre-tunnel-linux.html)
 - [MPLS testbed article](http://www.samrussell.nz/2015/12/mpls-testbed-on-ubuntu-linux-with.html)
