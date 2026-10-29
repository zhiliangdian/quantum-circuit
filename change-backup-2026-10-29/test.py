
import numpy as np
import data

"""
ket_0 = np.array([[1], [0]])
ket_1 = np.array([[0], [1]])

qubit_0 = elements.Qubit(qubit_state=ket_0)
qubit_1 = elements.Qubit(qubit_state=ket_1)
wire_0 = elements.Wire(sources=qubit_0)
wire_1 = elements.Wire(sources=qubit_1)
H_gate = elements.Hadamard(sources=wire_0).get_output()

print(H_gate)
"""

swap_gate = np.array([[1, 0, 0, 0],
                        [0, 0, 1, 0],
                        [0, 1, 0, 0],
                        [0, 0, 0, 1]])

I = np.array([[1, 0], [0, 1]])

