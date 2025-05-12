#!/usr/bin/env python3

"""
Example showing how "Extract" could be used to recycle legacy files
to build new ones.
"""

# Import mcnpgo
from mcnpgo.mcnpgo import *

# Loading files
room_45 = go("./results/room_45.mcnp") # Load old file

# Extract detector bench
detector = room_45.Extract(range(12,22), radius=10e2)

# Reverse it back to its original position
# (Header of "room_45.mcnp" contains information on what was done 
# to the detector bench, so that we can reverse transform it.)
detector.Translat([0,-400,0]) # Pure translation
detector.TrRotY(angle=-1)     # Pure rotation

# Place it inside experience room
detector.TrRotZ(angle=-90,trans=[200,300,0])

# Insert detector in experience room
# We need to use InsertCells since detector was extracted
room_45.InsertCells(detector)

# Save file
room_45.WriteMCNPFile("./results/newroom_45.mcnp")
