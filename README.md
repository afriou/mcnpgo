# MCNP-GO

MCNP-GO is a Python package designed to manipulate and assemble MCNP input files using a systems engineering approach. It allows users to assemble a set of independent objects, each described by a valid MCNP file, into a single cohesive file. This tool is particularly useful for radiation protection and tomographic experiments, where precise modeling and positioning of equipment are crucial.

## Features

- **File Assembly**: Assemble multiple MCNP input files into a single file.
- **Transformation**: Apply translations and rotations to position objects relative to each other.
- **Renumbering**: Automatically renumber cells, surfaces, and transformations to avoid conflicts.
- **Extraction**: Extract subsets of cells from existing files to create new independent objects.
- **Traceability**: Keep track of operations performed on files, enhancing traceability and ease of modification.
- **Material Management**: Merge and manage material cards during the assembly process.

