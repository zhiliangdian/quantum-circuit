# Quantum Circuit Simulator

A personal project exploring the simulation and visualisation of quantum circuits using Python.

The project aims to provide an interactive interface for constructing quantum circuits and examining the evolution of their quantum states.

## Current Features

Interactive circuit editor built with Matplotlib.
Draggable circuit elements and automatic connection detection.
Support for Hadamard and CNOT gates.
Configurable initial qubit states.
State-vector simulation using NumPy.
Calculation and display of the global quantum state at different stages of a circuit.

## Implementation

The project currently consists of two main components:

* **GUI (`gui.py`)**: Handles graphical elements, user interaction and circuit visualisation.
* **Data model (`data.py`, `elements.py`)**: Manages circuit elements, their connections and quantum state calculations.

Quantum gates are represented using tensor-product decompositions, allowing local operations to be applied to the global state vector.

## Dependency

This project has following dependecies so far:
Matplotlib
Numpy
Python 3.10+

## Limitations and Future Development

This project is still under active development. Several features, including quantum measurement, are not yet implemented.

Possible future improvements include:

Support X Z Y Measurement gates
Support classical logic operation
Make Hadamard gates extensiable
Rename variables and functions to make it more readable (I hate my ability to name things)
Optimization
Usage of density matrixes to replace the current amplitudes vectors

The next milestone would be to able to construct a quantum teleportation demo.
