#!/usr/bin/env python3

"""
Test script for merging material cards
"""

# Import mcnpgo
from mcnpgo.mcnpgo import *
from copy import deepcopy

# Loading files
detector = go("./detector.mcnp")
detector2 = go("./detector2.mcnp")
detector3 = go("./detector3.mcnp")
detector4 = go("./detector4.mcnp")
detector4_cpy = deepcopy(detector4)
detector5 = go("./detector5.mcnp")
detector6 = go("./detector6.mcnp")

# TEST 1

# Move detector2 and insert it
detector2.Translat([0,100,0])
detector.Insert(detector2)

# Save file
detector.WriteMCNPFile("./results/Test1.mcnp")


# TEST 2

# Insert detector 2
detector3.Insert(detector2)

# Save file
detector3.WriteMCNPFile("./results/Test2.mcnp")


# TEST 3

# Insert detector 2
detector4.Insert(detector2)

# Save file
detector4.WriteMCNPFile("./results/Test3.mcnp")


# TEST 4

# Insert detector 4
detector2_cpy = deepcopy(detector2)
detector2_cpy.Insert(detector4_cpy)

# Save file
detector2_cpy.WriteMCNPFile("./results/Test4.mcnp")


# TEST 5

# Insert detector 2
detector5.Insert(detector2)

# Save file
detector5.WriteMCNPFile("./results/Test5.mcnp")


# TEST 6

# Insert detector 2
detector6.Insert(detector2)

# Save file
detector6.WriteMCNPFile("./results/Test6.mcnp")


