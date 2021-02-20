Title: Working with IP Packager and Integrator in Vivado using Tcl
Date: 2021-02-20 13:00
Modified: 2021-02-20 13:00
Category: EDA
Tags: eda, vivado, tcl, ip, fpga
Slug: vivado-ips-with-tcl
Status: published

## Preface

Vivado's IP Integrator offers convenient access to its vast collection of production-grade IPs for the designer to incorporate into their designs.  Furthermore, they allow the designer to extend the experience to custom IP cores via the IP Packager, fostering better integration and promoting reuse within the Xilinx FPGA ecosystem.  Both the IP Integrator and IP Packager offer a GUI interface for straightforward access, but that can become quite tedious when working with larger designs with multiple IPs and/or multiple interfaces.  Fortunately, with the help of some short Tcl, both the IP packaging (in the IP Packager) and instantiation (in the IP Integrator, or more commonly known as a _Block Design_) can be automated.

### Quick note

Most of the affairs discussed in this article are, unlike other flows in Vivado, such as the Project/Non-Project Batch Mode, not very well documented.  The following materials provided most of the information:

- UG912: Vivado Design Suite Properties Reference Guide
- UG835: Vivado Design Suite Tcl Command Reference Guide
- output in the __Tcl Console__ when performing GUI 
- `help` command
- `report_property` command
- the Xilinx forum

## IP Packager: mapping ports in interfaces

The single most tedious process in packaging an IP is mapping the interfaces to top-level ports.  While IP Packager offers interface inference, it bails out on the slightest discrepancies between top-level port names and the interface definitions (such as Vivado v. Chisel for AXI4).  The interface definitions, as well as nearly all other functions in the IP Packager, can actually be manipulated with `ipx::*` commands; you can list them with `help ipx::*`.

Use `ips::add_bus_interface` to create an interface on the IP, set the abstraction type, bus type, and interface mode, and then create port maps with `ipx::add_port_map`.  For example, if we're adding a BRAM interface called `$portName`:

```tcl
set core [ipx::current_core]
set intf [ipx::add_bus_interface $portName $core]

set_property -dict [list \
    abstraction_type_vlnv xilinx.com:interface:bram_rtl:1.0 \
    bus_type_vlnv xilinx.com:interface:bram:1.0 \
    interface_mode master] $intf

# can be stored as a dict
set_property physical_name ${portName}_address [ipx::add_port_map ADDR $intf]
set_property physical_name ${portName}_din [ipx::add_port_map DOUT $intf]
set_property physical_name ${portName}_dout [ipx::add_port_map DIN $intf]
set_property physical_name ${portName}_ce [ipx::add_port_map EN $intf]
set_property physical_name ${portName}_we [ipx::add_port_map WE $intf]
```

The above snippet is basically copied from the Tcl window after manually mapping one interface by hand.  The defining keys for a BRAM interface are the abstract and bus VLNVs, which can be found in the command outputs.  By storing the port map and bus interface objects, we can save time from the excessive `ipx::get_port_maps` and `ipx::get_bus_interfaces` commands.  After testing the snippet out, it can then be incorporated into a `proc` to be used in further automation.

## IP Integrator: building a block design

The block design can be built with Tcl calls rather than adding blocks and dragging connections between them, which quickly gets pretty tedious when more blocks get involved.  You can choose to build from scratch, or base on the results from __Export Block Design__.

### Instantiating blocks and connecting nets

`create_bd_cell` is used to create about every type of BD cells, but in most cases we care about IPs the most.  `set_property` is then used to customize the IP.  For example, to create a Block Memory Generator that is a true dual port memory, as well as the corresponding controller:

```tcl
set bmgName bmg_0
set bmg [create_bd_cell -type ip -vlnv xilinx.com:ip:blk_mem_gen:8.4 $bmgName]
set_property -dict [list \
    CONFIG.Memory_Type {True_Dual_Port_RAM} \
    CONFIG.Assume_Synchronous_Clk {true}] $bmg
    
set axiCtrlName axi_bram_ctrl_0
set axiCtrl [create_bd_cell -type ip -vlnv xilinx.com:ip:axi_bram_ctrl:4.1 $axiCtrlName]
```

Remember that the possible properties of a cell can be consulted via `report_property -all`.  Make sure to check the reports and follow the RW/RO limitations, or the IP may misbehave.

`connect_bd_net` is used to create simple nets (i.e. non-interfaces) while `connect_bd_intf_net` is for interfaces (e.g. AXI4, BRAM).  `get_bd_{,intf_}{pins,ports}` can be used to find a port/pin by path.  As we're using paths, saving the path name in a variable for later access will most likely be convenient.  The following snippet assumes the pins `$clk` `$rstn` and `$axiM` hold the clock, active-low synchronous reset, and master AXI pins.

```tcl
foreach a {A B} {
    connect_bd_intf_net [get_bd_intf_pins $axiCtrlName/BRAM_PORT$a] [get_bd_intf_pins $bmgName/BRAM_PORT$a]
}
connect_bd_intf_net $axiM [get_bd_intf_pins $axiCtrlName/S_AXI]
connect_bd_net $clk [get_bd_pins $axiCtrlName/s_axi_aclk]
connect_bd_net $rstn [get_bd_pins $axiCtrlName/s_axi_aresetn]
```

### Mapping address segments

There are two types of address segments in a block design for a specific IP such as the BRAM: 

- A slave segment on an IP, which defines a mappable memory area
- A segment in the master address space corresponding to a slave segment

`get_bd_addr_segs` uses paths to locate both kinds, so it's important to distinguish these two kinds correctly.  `assign_bd_address` can be used to automatically assign (map) a slave segment into the master space.  `set_property` can then be used on the newly-created segment to modify its `range` or `offset`.  In the following snippet, we map the AXI BRAM controller into `0xdead0000` (stored in `$newOffset`).  We assume that the master is called `$masterName` and the address space is `$addrSpaceName`.

```tcl
# Slave Interface: S_AXI | Base Name: Mem0
assign_bd_address [get_bd_addr_segs $axiCtrlName/S_AXI/Mem0]
set_property range $newOffset [get_bd_addr_segs $masterName/$addrSpaceName/SEG_${axiCtrlName}_Mem0]
```

### Making hierarchies

When the connections and address assignments are done, grouping automatically generated BD components into hierarchies is usually desirable.  `group_bd_cells` is used for this purpose.  `move_bd_cells` can be used to add a cell to an existing hierarchy.

```tcl
set hierName hier_0
group_bd_cells $hierName $bmg $axiCtrl
```

Note that after creating a hierarchy, the paths for member cells will change, which may invalidate stored paths.

### Validate & save design

_Validate design_ is an important step which allows IPs to propagate their parameters to connecting IPs.  This mechanism supports various features such as width negotiation (bus or interface), link type negotiation (AXI4 or AXI4-Lite), and more complicated parameter propagation (such as BRAM operation mode).  The following snippet validates, reorganizes (GUI-wise), and saves the current block design:

```tcl
validate_bd_design
regenerate_bd_layout
save_bd_design
```

### Note on built-in BD automation

While it is possible to use `apply_bd_automation` to simulate the automation process in block designs (e.g. instantiating BMGs or connecting AXIs), I recommend refraining from that and still connect things with explicit commands.  This eliminates most surprises.