# MCNP-GO

MCNP-GO is a Python package designed to manipulate and assemble MCNP input files, allowing users to assemble a set of independent objects, each described by a valid MCNP file, into a single cohesive file. This tool is particularly useful for applications where precise modeling and positioning of equipment are crucial.

## Features

- **File Assembly**: Assemble multiple MCNP input files into a single file.
- **Transformation**: Apply translations and rotations to position objects relative to each other.
- **Renumbering**: Automatically renumber cells, surfaces, and transformations to avoid conflicts.
- **Extraction**: Extract subsets of cells from existing files to create new independent objects.
- **Traceability**: Keep track of operations performed on files, enhancing traceability and ease of modification.
- **Material Management**: Merge and manage material cards during the assembly process.

## Installation

To install MCNP-GO, you can use pip:
```sh
pip install setup.py
```

## Basic usage

This code reads two files, rotates one by 45 degrees and assembles them. For more details, the attached article is a good introduction to the library.

```python
from mcnpgo.mcnpgo import *

# Load MCNP files
obj1 = go("object1.mcnp")
obj2 = go("object2.mcnp")

# Apply transformations if necessary
obj1.TrRotZ(angle=45)  # Rotate obj1 by 45 degrees around the Z-axis

# Assemble files
obj2.Insert(obj1)

# Save the assembled file
obj2.WriteMCNPFile("assembled_file.mcnp")
```


## Requirements and caveats

In order to be able to assemble two files together, i.e. to insert one file in an other, the cell block cards must possess a particular structure. Consider the following cell block cards:
```
1 83 -7.13 -1                         $ scintillator
2 13 -2.7  -2 3                       $ scintillator cover
3 13 -2.7  -4 5 1                     $ detector box
4 26 -7.9  -6                         $ base steel plate
6 14 -2.4  -9                         $ mirror
10 100 -1.205e-3 (1 #3 9) (-3:-4)     $ air
11 0 (6 4 2)                          $ graveyard
```
The last two cells, 10 and 11, are remarkable:
- The second-to-last cell describes the ambient medium (here, air) in which bathe the other cells, and this is the only cell like this. 
- The last cell describes the external world (where particles are killed). In this cell, surfaces 6, 4 and 2, define the bounding surface, delimiting the external world from the interior.   
The only prerequisite required by the tool is to place the cell describing the ambient medium in the second-to-last position, and that describing the external world in the last position. This structuring is generally very easy to achieve. Note that this is necessary only for the package insert feature. The other features do not require any particular structuring of the file. As we shall see, inserting a file into another is based in part on the boundary surface of the object.

The function of MCNP-GO that interprets MCNP files is not as efficient as the one implemented in the MCNP code. While it could be perfected with more developments, a few caveats still exists:
- A card description should not be interrupted by a comment line (starting with "c"). Rather, comment using the dollar symbol at the end of the line.
- Vertical input format is not implemented.
- Universes and fill cards must be defined in the cell block.

MCNP-GO tries to catch and correct the input file and issues warnings, but exceptions might still occur. In particular, the output file is formatted as little as possible, in order to facilitate comparison between input files and the final (assembled) output file.	


