from dataclasses import dataclass
import data
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
        _delay: The time delay at the element.
    """
    def __init__(self, sources = None, target = None, delay = 0):
        """
        This is the constructor for the element class. It initializes the qubit states, sources, target, and delay of the element.
        """
        self.set_sources(editor = self, new_sources=sources)
        self.set_target(editor = self, new_target=target)
        self._delay = delay

    def get_qubit_states(self):
        return self._qubit_states

    def get_sources(self):
        return self._sources

    def get_target(self):
        return self._target
    
    def set_sources(self, editor, new_sources):
        if isinstance(editor, (data.Model, Element, Qubit)):
            self._sources = new_sources
            if new_sources is not None and new_sources.get_target() is not self:
                new_sources.set_target(editor = self, new_target=self)
        else:
            raise ValueError("data in elements must be edited from data layer")
        self.refresh_qubits()

    def set_target(self, editor, new_target):
        if isinstance(editor, (data.Model, Element)):
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

    def get_total_delay(self):
        """
        This method returns the total delay at the element.
        """
        if self.get_sources() is not None:
            return self.get_sources().get_total_delay() + self._delay
        return self._delay

    def get_initial_sources(self):
        """
        Return a flat list of initial qubits in input order.
        """
        if self.get_sources() is not None:
            return self.get_sources().get_initial_sources()
        return []


class Wire(Element):
    """
    This class represents a wire in the quantum circuit, which connects two other elements.
    """
    def __init__(self, sources=None, target=None, delay=0):
        super().__init__(sources, target, delay)

    def set_delay(self, editor, new_delay):
        if isinstance(editor, (data.Model, Wire)):
            self._delay = new_delay
        else:
            raise ValueError("data in elements must be edited from data layer")
        
    def get_delay(self):
        """
        This method returns the total delay at the wire.
        """
        return self._delay

    def get_total_delay(self):
        """
        This method returns the total delay at the wire, including the delay of its sources.
        """
        if self.get_sources() is not None:
            return self.get_sources().get_total_delay() + self._delay
        return self._delay


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
        if type(editor) == data.Model or editor == self:
            self._qubit_states = new_states
        else:
            raise ValueError("data in elements must be edited from data layer")

    def set_target(self, editor, new_target):
        if isinstance(editor, (data.Model, Qubit, Element)):
            self._target = new_target
            if new_target is not None and new_target.get_sources() is not self:
                new_target.set_sources(editor = self, new_sources = self)
        else:
            raise ValueError("data in elements must be edited from data layer")

    def get_qubit_states(self):
        return self._qubit_states

    def get_target(self):
        return self._target

    def get_total_delay(self):
        return 0

    def get_initial_sources(self):
        return [self]


class Gate(Element):
    """
    This  is the parent class for all gates in the quantum circuit.
    """
    def __init__(self, sources=None, target=None, qubit_number=1):
        super().__init__(sources=sources, target=target)
        self._qubit_number = qubit_number
        self._output = self.transformation()

    def transformation(self):
        """
        This method applies the gate's transformation to the input qubit states and returns the output qubit states.
        """
        return self.get_matrix() @ self.combine_entry()

    def get_matrix(self):
        return self._matrix

    def get_qubit_states(self):
        return self._output

    def combine_entry(self):
        """
        this method combines the input qubits states into a single state vector for the gate's transformation.
        """
        combined_state = self.get_sources()[0].get_qubit_states()
        for source in self.get_sources()[1:]:
            combined_state = np.kron(combined_state, source.get_qubit_states())
        return combined_state

    def get_total_delay(self):
        """
        This method returns the total delay at the gate, including the delay of its sources.
        """
        if self.get_sources() is not None:
            return max(source.get_total_delay() for source in self.get_sources())
        return 0

    def get_base_matrixes(self):
        """
        This method returns the matrix composition of the gate in the form of 
        M1 ⊗ M2 ⊗... +  M3 ⊗ M4 ⊗... + ..., 
        in the form of
        [[M1, M2, ...], [M3, M4, ...], ...]
        """
        pass

    def get_initial_sources(self):
        """
        Return a flat list of initial qubits in input order.
        """
        if self.get_sources() is not None:
            initial_sources = []
            for source in self.get_sources():
                initial_sources.extend(source.get_initial_sources())
            return initial_sources
        return []


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
    def __init__(self, sources=None, target=None, qubit_number = 1):
        self._qubit_number = qubit_number #this line is here to prevent circular defining
        
        self._matrix = np.eye(1)
        for i in self.get_base_matrixes()[0]:
            self._matrix = np.kron(self._matrix, i)
        super().__init__(sources=sources, target=target, qubit_number=qubit_number)
        print(self._qubit_number)

    def get_base_matrixes(self):
        return np.array([
            [np.array([[1, 1],
                       [1, -1]]) / np.sqrt(2) for _ in range(self._qubit_number)]
            ])


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
    def __init__(self, sources=None, target=None, qubit_number = 2):
        self._matrix = np.array([[1, 0, 0, 0],
                                  [0, 1, 0, 0],
                                  [0, 0, 0, 1],
                                  [0, 0, 1, 0]])
        super().__init__(sources=sources, target=target, qubit_number=qubit_number)
    
    def get_base_matrixes(self):
        return np.array([
            [np.array([[1, 0],
                        [0, 0]]),
              np.array([[1, 0], 
                        [0, 1]])], 
            [np.array([[0, 0], 
                       [0, 1]]), 
              np.array([[0, 1], 
                        [1, 0]])]
              ])


class Measurement(Gate):
    """
    This is the Measurement gate.
    It measures the qubit states and collapses them to classical bits.
    """
    def __init__(self, sources=None, target=None, qubit_number = 1):
        self._matrix = np.eye(2**qubit_number)
        super().__init__(sources=sources, target=target, qubit_number=qubit_number)

    def transformation(self):
        """
        This method applies the measurement to the input qubit states and returns the output classical bits.
        """
        qubit_states = self.combine_entry()
        probabilities = np.abs(qubit_states)**2
        measured_state = np.random.choice(len(probabilities), p=probabilities)
        output_state = np.zeros_like(qubit_states)
        output_state[measured_state] = 1
        return output_state

Hadamard()
