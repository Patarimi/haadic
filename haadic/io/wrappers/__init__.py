"""
Wrapper modules for different simulation tools.

This wrappers are based on nix (for Linux and MacOS) and WSL (for Windows).
They all defined a compute function that takes as input the necessary files for the simulation and runs the simulation,
returning the results in a standardized format (e.g., a scikit RF network for EMX, a dictionary of performance metrics for
post-processing).

The tools submodules contains functions to wrap nix call for both Linux/MacOS and Windows (WSL).
"""
