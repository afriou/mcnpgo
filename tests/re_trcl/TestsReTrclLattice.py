#!/usr/bin/env python3

"""
Test script for ResolveTRCL on lattices.
"""

# Import mcnpgo
import os
from mcnpgo.mcnpgo import *

# Listing test files
files = [file for file in os.listdir() if os.path.isfile(file) and file.endswith(".mcnp")]

# Transform on thoses files
for file in files:

    # Load file
    lat = go(file)

    # Renumbering to have surfaces or cells > 1000
    print("Testing:" + file)
    lat.Renum(cell=1,surf=7000,trans=30)

    # Renumbering for trcl
    lat.ResolveTRCL()

    # Save file
    lat.WriteMCNPFile("./results/Test_" + file)


