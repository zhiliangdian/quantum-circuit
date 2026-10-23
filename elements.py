from dataclasses import dataclass
from data import Data
import numpy as np

@dataclass(frozen=True)
class Element:
    """
    A base class for all elements in the quantum circuit.
    This includes wires, qubits, and gates.
    Methods:
        get_qubit_states(): Returns the qubit states of the element.
        get_sources(): Returns the sources of the element.
        get_target(): Returns the target of the element.
        set_qubit_states(editor, new_states): Sets the qubit states of the element. 
            This method can only be called from the Data or element class.
        set_sources(editor, new_sources): Sets the sources of the element. 
            This method can only be called from the Data or element class.
        set_target(editor, new_target): Sets the target of the element. 
            This method can only be called from the Data or element class.
    Attributes:
        _qubit_states:  The qubit states of the element.
        _sources: The source of the element.
        _target: The target of the element.
    """
    def __init__(self, sources = None, target = None):
        """
        This is the constructor for the element class. It initializes the qubit states, sources, and target of the element.
        """
        self.set_sources(editor = self, new_sources=sources)
        self.set_target(editor = self, new_target=target)

    def get_qubit_states(self):
        return self._qubit_states

    def get_sources(self):
        return self._sources

    def get_target(self):
        return self._target
    
    def set_sources(self, editor, new_sources):
        if isinstance(editor, (Data, Element, Qubit)):
            self._sources = new_sources
            if new_sources is not None and new_sources.get_target() is not self:
                new_sources.set_target(editor = self, new_target=self)
        else:
            raise ValueError("data in elements must be edited from data layer")
        self.refresh_qubits()

    def set_target(self, editor, new_target):
        if isinstance(editor, (Data, Element)):
            self._target = new_target
            if new_target is not None and new_target.get_sources() is not self:
                new_target.set_sources(editor = self, new_sources=self)
        else:
            raise ValueError("data in elements must be edited from data layer")

    def refresh_qubits(self):
        """
        This method refreshes the qubit states of the element.
        """
        self._qubit_states = self.get_sources().get_qubit_states()


class Wire(Element):
    """
    This class represents a wire in the quantum circuit, which connects two other elements.
    """
    def __init__(self, sources=None, target=None):
        super().__init__(sources, target)

class Qubit():
    """
    This class represents a qubit sources in the quantum circuit.
    """
    def __init__(self, qubit_state, target=None):
        """
        This is the constructor for the qubit class. It takes a single qubit state and an optional target element as input.
        It does not have a sources.
        """
        self.set_qubit_states(editor = self, new_states = qubit_state)
        self.set_target(editor = self, new_target = target)

    def set_qubit_states(self, editor, new_states):
        if type(editor) == Data or editor == self:
            self._qubit_states = new_states
        else:
            raise ValueError("data in elements must be edited from data layer")

    def set_target(self, editor, new_target):
        if isinstance(editor, (Data, Qubit, Element)):
            self._target = new_target
            if new_target is not None and new_target.get_sources() is not self:
                new_target.set_sources(editor = self, new_sources = self)
        else:
            raise ValueError("data in elements must be edited from data layer")

    def get_qubit_states(self):
        return self._qubit_states

    def get_target(self):
        return self._target

class Gate(Element):
    """
    This  is the parent class for all gates in the quantum circuit.
    """
    def __init__(self, sources=None, target=None):
        super().__init__(sources=sources, target=target)
        self._output = self.transformation()

    def transformation(self):
        """
        This method applies the gate's transformation to the input qubit states and returns the output qubit states.
        """

        return self.get_matrix() @ self.get_qubit_states()

    def get_matrix(self):
        return self._matrix

    def get_output(self):
        return self._output

class Hadamard(Gate):
    """
    This is the Hadamard gate.
    Matrix representation:
        1/sqrt(2) * [[1, 1],
                     [1, -1]]
    operator representation:
        H = 1/sqrt(2) * (|0><0| + |0><1| + |1><0| - |1><1|)
    it transforms |0> to |+> and |1> to |->.
    """
    def __init__(self, sources=None, target=None):
        self._matrix = (1/np.sqrt(2)) * np.array([[1, 1], [1, -1]])
        super().__init__(sources=sources, target=target)

class CNOT(Gate):
    """
    This is the CNOT gate.
    Matrix representation:
        [[1, 0, 0, 0],
         [0, 1, 0, 0],
         [0, 0, 0, 1],
         [0, 0, 1, 0]]
    operator representation:
        CNOT = |00><00| + |01><01| + |10><11| + |11><10|
    it flips the target qubit if the control qubit is |1>.
    """
    def __init__(self, sources=None, target=None):
        self._matrix = np.array([[1, 0, 0, 0],
                                  [0, 1, 0, 0],
                                  [0, 0, 0, 1],
                                  [0, 0, 1, 0]])
        super().__init__(sources=sources, target=target)