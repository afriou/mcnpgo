#!/usr/bin/env python3

"""
Test script for transformation of lattices.
"""

import os,sys
sys.path.append("../../")
from mcnpgo.mcnpgo import *

# Listing test files
files = [file for file in os.listdir() if os.path.isfile(file) and file.endswith(".mcnp")]

# Read and write files
for file in files:

    # Load file
    lat = go(file)

    # Save file
    lat.WriteMCNPFile("./results/Test_" + file)


