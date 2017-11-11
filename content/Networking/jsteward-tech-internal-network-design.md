Title: JSteward Tech Internal Network Design
Date: 2017-11-11 15:00
Modified: 2017-11-11 15:00
Category: Networking
tags: networking, infrastructure
Slug: jsteward-tech-internal-network-design

## Preface

As the number of machines that belong to me increase gradually, it has become a necessity to connect the machines
together with secure, reliable tunnels, thus forming an internal network. A private network can have the following
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
The both ends should authenticate each other through X.509 certificates, issued by the PKI managed by JSteward Tech.

### **Client** to **server**

The client should establish a VPN session to the server, with one of the following protocols:

 - IKEv2
 - IPsec Hybrid RSA

### **Client** to **small router**

The client should connect to the small router directly via physical medium, such as an ethernet cable or a WiFi connection.
