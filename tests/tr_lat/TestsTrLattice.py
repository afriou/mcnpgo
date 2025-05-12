#!/usr/bin/env python3

"""
Test script for transformation of lattices.
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

    # Transform file
    print("Testing:" + file)
    lat.TrRotZ(angle=45,trans=[25,0,0])
    lat.TrRotY(angle=90,trans=[0,0,25])
    # Lattice should be centered in YZ plane

    # Save file
    lat.WriteMCNPFile("./results/Test_" + file)


