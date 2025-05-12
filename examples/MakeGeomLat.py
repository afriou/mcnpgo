#!/usr/bin/env python3


import os,sys
sys.path.append("../")
from mcnpgo.mcnpgo import *
from copy import deepcopy

# Loading files
room = go("./room.mcnp")
detector = go("./detector.mcnp")
ccd = go("./ccd.mcnp")
lat = go("./lat_ex5.mcnp")

# Start by placing the CCD + lead in detector
ccd.Translat([60,50,0])
detector.Insert(ccd, location = 'inside')

# Moving detector+ccd
# Detector bench was tilted by 1° around axis Y
detector.TrRotY(trans=[0,400,0],angle=1)

# Insert detector in experience room
room.Insert(detector, location = 'inside')

# Create directory
# os.system("mkdir -p results")

# Loop over test object angles
angles = [0,30,45,90]
for d in angles:
    # Local copy of lattice and room
    lat_cpy = deepcopy(lat)
    room_cpy = deepcopy(room)

    # Shift and rotate
    lat_cpy.TrRotZ(trans=[0,300,0],angle=d)

    # Insert in room
    room_cpy.Insert(lat_cpy, location = 'inside')


    """
    We now add cards other than geometry related to the file.
    This needs to be done just before WriteMCNPFile as Insert functions will
    destroy card informations other than geometry related.
    """

    # Header
    room_cpy.AddMCNPBanner("PHYSICS")

    # Add physics cards
    lsCard = list()
    lsCard.append("MODE N P E")
    lsCard.append("PHYS:N 30.0")
    lsCard.append("PHYS:P 30.0")
    lsCard.append("PHYS:E 30.0 6j 0")
    lsCard.append("c")
    lsCard.append("CUT:P  J 0.05")
    lsCard.append("CUT:E  J 0.05")
    room_cpy.AddMCNPCard(lsCard)

    # Add tallies from json infos stored at the end of mcnp files
    # Header
    room_cpy.AddMCNPBanner("TALLIES")

    # Photon Kerma in scintillator cell
    room_cpy.AddMCNPTally(group="ScintillatorCell",tally = "F4:P",card=["FM -1 83 -5 -6"])

    # Point detector tally 1 meter from source
    room_cpy.AddMCNPPointTally(group="room_F5",part="P")

    # Save file
    room_cpy.WriteMCNPFile(f"./results/room_{d}.mcnp")
