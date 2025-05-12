#!/usr/bin/env python3

"""
Test script for re-numbering of lattices.
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

    # Renumbering
    print("Testing:" + file)
    lat.Renum(cell=20,surf=10,trans=30)

    # Save file
    lat.WriteMCNPFile("./results/Test_" + file)


