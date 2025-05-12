#!/usr/bin/env python3

# Entete a recopier
import os,sys
sys.path.append("../../")
from mcnpgo.mcnpgo import *
from copy import deepcopy

# Loading files
room_30 = go("./room_30.mcnp") # Load old file

# Extract detector bench
detector = room_30.Extract(range(12,22), radius=10e2)

# Save file
detector.WriteMCNPFile("./results/detector.mcnp")


# Extract lattice
lat = room_30.Extract(range(1,12), radius=10e2)

# Save file
lat.WriteMCNPFile("./results/lat.mcnp")


# Extract evrything but lattice
room_30_but_lat = room_30.Extract(range(1,12), mode='subtract', radius=10e2)

# Save file
room_30_but_lat.WriteMCNPFile("./results/room_30_but_lat.mcnp")
