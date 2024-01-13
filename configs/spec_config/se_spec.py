import argparse
import sys
import os

import m5
from m5.defines import buildEnv
from m5.objects import *
from m5.params import NULL
from m5.util import addToPath, fatal, warn

addToPath("../")

#from ruby import Ruby

#from common import Options
from common import Simulation
from common import CacheConfig
from common import CpuConfig
from common import ObjectList
from common import MemConfig
from common.FileSystemConfig import config_filesystem
from common.Caches import *
from common.cpu2000 import *

def add_options(parser):
    parser.add_argument("-n", "--num-cpus", type=int, default=1)
    parser.add_argument(
        "--sys-voltage",
        action="store",
        type=str,
        default="1.0V",
        help="""Top-level voltage for blocks running at system
                      power supply""",
    )
    parser.add_argument(
        "--sys-clock",
        action="store",
        type=str,
        default="1GHz",
        help="""Top-level clock for blocks running at system
                      speed""",
    )

    parser.add_argument(
        "--mem-type",
        default="DDR3_1600_8x8",
        choices=ObjectList.mem_list.get_names(),
        help="type of memory to use",
    )
    parser.add_argument(
        "--mem-channels", type=int, default=1, help="number of memory channels"
    )
    parser.add_argument(
        "--mem-ranks",
        type=int,
        default=None,
        help="number of memory ranks per channel",
    )
    parser.add_argument(
        "--mem-size",
        action="store",
        type=str,
        default="512MB",
        help="Specify the physical memory size (single memory)",
    )
    parser.add_argument(
        "--enable-dram-powerdown",
        action="store_true",
        help="Enable low-power states in DRAMInterface",
    )
    parser.add_argument(
        "--mem-channels-intlv",
        type=int,
        default=0,
        help="Memory channels interleave",
    )

    parser.add_argument("--memchecker", action="store_true")

    # Cache Options
    parser.add_argument(
        "--external-memory-system",
        type=str,
        help="use external ports of this port_type for caches",
    )
    parser.add_argument(
        "--tlm-memory",
        type=str,
        help="use external port for SystemC TLM cosimulation",
    )
    parser.add_argument("--caches", action="store_true")
    parser.add_argument("--l2cache", action="store_true")
    parser.add_argument("--num-dirs", type=int, default=1)
    parser.add_argument("--num-l2caches", type=int, default=1)
    parser.add_argument("--num-l3caches", type=int, default=1)
    parser.add_argument("--l1d_size", type=str, default="64kB")
    parser.add_argument("--l1i_size", type=str, default="32kB")
    parser.add_argument("--l2_size", type=str, default="2MB")
    parser.add_argument("--l3_size", type=str, default="16MB")
    parser.add_argument("--l1d_assoc", type=int, default=2)
    parser.add_argument("--l1i_assoc", type=int, default=2)
    parser.add_argument("--l2_assoc", type=int, default=8)
    parser.add_argument("--l3_assoc", type=int, default=16)
    parser.add_argument("--cacheline_size", type=int, default=64)

    # Enable Ruby
    parser.add_argument("--ruby", action="store_true")

    # Run duration options
    parser.add_argument(
        "-m",
        "--abs-max-tick",
        type=int,
        default=m5.MaxTick,
        metavar="TICKS",
        help="Run to absolute simulated tick "
        "specified including ticks from a restored checkpoint",
    )
    parser.add_argument(
        "--rel-max-tick",
        type=int,
        default=None,
        metavar="TICKS",
        help="Simulate for specified number of"
        " ticks relative to the simulation start tick (e.g. if "
        "restoring a checkpoint)",
    )
    parser.add_argument(
        "--maxtime",
        type=float,
        default=None,
        help="Run to the specified absolute simulated time in seconds",
    )
    parser.add_argument(
        "-P",
        "--param",
        action="append",
        default=[],
        help="Set a SimObject parameter relative to the root node. "
        "An extended Python multi range slicing syntax can be used "
        "for arrays. For example: "
        "'system.cpu[0,1,3:8:2].max_insts_all_threads = 42' "
        "sets max_insts_all_threads for cpus 0, 1, 3, 5 and 7 "
        "Direct parameters of the root object are not accessible, "
        "only parameters of its children.",
    )
def addCommonOptions(parser):
    # start by adding the base options that do not assume an ISA
    #addNoISAOptions(parser)

    # system options

    parser.add_argument(
        "--bp-type",
        default=None,
        choices=ObjectList.bp_list.get_names(),
        help="""
                        type of branch predictor to run with
                        (if not set, use the default branch predictor of
                        the selected CPU)""",
    )
    parser.add_argument(
        "--indirect-bp-type",
        default=None,
        choices=ObjectList.indirect_bp_list.get_names(),
        help="type of indirect branch predictor to run with",
    )
    parser.add_argument(
        "--l1i-hwp-type",
        default=None,
        choices=ObjectList.hwp_list.get_names(),
        help="""
                        type of hardware prefetcher to use with the L1
                        instruction cache.
                        (if not set, use the default prefetcher of
                        the selected cache)""",
    )
    parser.add_argument(
        "--l1d-hwp-type",
        default=None,
        choices=ObjectList.hwp_list.get_names(),
        help="""
                        type of hardware prefetcher to use with the L1
                        data cache.
                        (if not set, use the default prefetcher of
                        the selected cache)""",
    )
    parser.add_argument(
        "--l2-hwp-type",
        default=None,
        choices=ObjectList.hwp_list.get_names(),
        help="""
                        type of hardware prefetcher to use with the L2 cache.
                        (if not set, use the default prefetcher of
                        the selected cache)""",
    )
    parser.add_argument("--checker", action="store_true")
    parser.add_argument(
        "--cpu-clock",
        action="store",
        type=str,
        default="2GHz",
        help="Clock for blocks running at CPU speed",
    )
    parser.add_argument(
        "--smt",
        action="store_true",
        default=False,
        help="""
                      Only used if multiple programs are specified. If true,
                      then the number of threads per cpu is same as the
                      number of programs.""",
    )
    parser.add_argument(
        "--elastic-trace-en",
        action="store_true",
        help="""Enable capture of data dependency and instruction
                      fetch traces using elastic trace probe.""",
    )




def addSEOptions(parser):
    # Benchmark options
    parser.add_argument(
        "-c",
        "--cmd",
        default="",
        help="The binary to run in syscall emulation mode.",
    )
    parser.add_argument(
        "-e",
        "--env",
        default="",
        help="Initialize workload environment from text file.",
    )
    parser.add_argument(
        "-i", "--input", default="", help="Read stdin from a file."
    )
    parser.add_argument(
        "--output", default="", help="Redirect stdout to a file."
    )
    parser.add_argument(
        "--errout", default="", help="Redirect stderr to a file."
    )


parser = argparse.ArgumentParser()
add_options(parser)
addCommonOptions(parser)
addSEOptions(parser)

args = parser.parse_args()
print(args)
## set cpu simulation system
system = System(
    cpu=RiscvO3CPU(),
    mem_mode="timing",
    mem_ranges=[AddrRange(args.mem_size)],
    cache_line_size=args.cacheline_size,
)

# Create a top-level voltage domain
system.voltage_domain = VoltageDomain(voltage=args.sys_voltage)

# Create a source clock for the system and set the clock period
system.clk_domain = SrcClockDomain(
    clock=args.sys_clock, voltage_domain=system.voltage_domain
)

# Create a CPU voltage domain
system.cpu_voltage_domain = VoltageDomain()

# Create a separate clock domain for the CPUs
system.cpu_clk_domain = SrcClockDomain(
    clock=args.cpu_clock, voltage_domain=system.cpu_voltage_domain
)
for cpu in system.cpu:
    cpu.clk_domain = system.cpu_clk_domain
    





