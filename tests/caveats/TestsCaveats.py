#!/usr/bin/env python3

"""
Test script for caveats
"""

import sys
sys.path.append("../../")
from mcnpgo.mcnpgo import *

# TEST 1

# Loading files
detector = go("./detector1.mcnp")

# Save file
detector.WriteMCNPFile("./results/Test1.mcnp")



