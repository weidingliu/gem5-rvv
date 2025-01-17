# Copyright (c) 2018 ARM Limited
# All rights reserved.
#
# The license below extends only to copyright in the software and shall
# not be construed as granting a license to any other intellectual
# property including but not limited to intellectual property relating
# to a hardware implementation of the functionality of the software
# licensed hereunder.  You may use the software subject to the license
# terms below provided that you ensure that this notice is replicated
# unmodified and in its entirety in all distributions of the software,
# modified or unmodified, in source code or in binary form.
#
# Copyright (c) 2005-2007 The Regents of The University of Michigan
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met: redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer;
# redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution;
# neither the name of the copyright holders nor the names of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from m5.params import *
from m5.proxy import *
from m5.util.fdthelper import *
from m5.defines import buildEnv

from m5.objects.Device import BasicPioDevice
from m5.objects.Serial import SerialDevice


class Uart(BasicPioDevice):
    type = "Uart"
    abstract = True
    cxx_header = "dev/serial/uart.hh"
    cxx_class = "gem5::Uart"
    platform = Param.Platform(Parent.any, "Platform this device is part of.")
    device = Param.SerialDevice(Parent.any, "The terminal")


class SimpleUart(Uart):
    type = "SimpleUart"
    cxx_header = "dev/serial/simple.hh"
    cxx_class = "gem5::SimpleUart"
    byte_order = Param.ByteOrder("little", "Device byte order")
    pio_size = Param.Addr(0x4, "Size of address range")
    end_on_eot = Param.Bool(
        False, "End the simulation when a EOT is received on the UART"
    )


class Uart8250(Uart):
    type = "Uart8250"
    cxx_header = "dev/serial/uart8250.hh"
    cxx_class = "gem5::Uart8250"
    pio_size = Param.Addr(0x8, "Size of address range")


class RiscvUart8250(Uart8250):
    def generateDeviceTree(self, state):
        node = self.generateBasicPioDeviceNode(
            state, "uart", self.pio_addr, self.pio_size
        )
        platform = self.platform.unproxy(self)
        plic = platform.plic
        node.append(FdtPropertyWords("interrupts", [platform.uart_int_id]))
        node.append(FdtPropertyWords("clock-frequency", [0x384000]))
        node.append(FdtPropertyWords("interrupt-parent", state.phandle(plic)))
        node.appendCompatible(["ns8250", "ns16550a"])
        yield node
