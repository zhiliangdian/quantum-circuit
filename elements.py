from dataclasses import dataclass
import data
import numpy as np

@dataclass(frozen=True, eq=False)
class Element:
    """
    A base class for all elements in the quantum circuit.
    This includes wires, qubits, and gates.
    Each connection slot is None or (other_element, other_port_index).
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

    # def get_qubit_states(self):
        # return self._qubit_states

    def get_sources(self):
        return self._sources

    def get_target(self):
        return self._target
    
    def set_sources(self, editor, new_sources, index=None):
        """Set the input list, or one input slot when index is supplied."""
        if isinstance(editor, (data.Model, Element, Qubit)):
            if index is not None:
                self._sources[index] = new_sources
            else:
                self._sources = (list(new_sources) if isinstance(new_sources, list)
                                 else [new_sources] * getattr(self, "_qubit_number", 1))
        else:
            raise ValueError("data in elements must be edited from data layer")

    def set_target(self, editor, new_target, index=None):
        """Set the output list, or one output slot when index is supplied."""
        if isinstance(editor, (data.Model, Element)):
            if index is not None:
                self._target[index] = new_target
            else:
                self._target = (list(new_target) if isinstance(new_target, list)
                                else [new_target] * getattr(self, "_qubit_number", 1))
        else:
            raise ValueError("data in elements must be edited from data layer")

    # def refresh_qubits(self):
        # """
        # This method refreshes the qubit states of the element.
        # """
        # sources = self.get_sources()
        # if sources is not None:
            # self._qubit_states = [source.get_qubit_states() for source in sources if source is not None]
        # else:
            # self._qubit_states = None

    def get_total_delay(self):
        return max((connection[0].get_total_delay()
                    for connection in self.get_sources() if connection is not None),
                   default=0) + self._delay

    def get_initial_sources(self, index=None):
        """Trace each output through its matching input; preserve empty slots."""
        if index is not None:
            connection = self.get_sources()[index]
            if connection is None:
                return [None]
            source, source_index = connection
            return source.get_initial_sources(source_index)
        return [self.get_initial_sources(i)[0] for i in range(len(self.get_sources()))]


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
        return super().get_total_delay()


class Qubit():
    """
    This class represents a qubit sources in the quantum circuit.
    """
    def __init__(self, qubit_state = np.array([[1], [0]]), target=None):
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

    def set_target(self, editor, new_target, index=None):
        """Set the output list, or one output slot when index is supplied."""
        if isinstance(editor, (data.Model, Qubit, Element)):
            if index is not None:
                self._target[index] = new_target
            else:
                self._target = list(new_target) if isinstance(new_target, list) else [new_target]
        else:
            raise ValueError("data in elements must be edited from data layer")

    def get_qubit_states(self):
        return self._qubit_states

    def get_target(self):
        return self._target

    def get_total_delay(self):
        return 0

    def get_initial_sources(self, index=None):
        if index not in (None, 0):
            raise IndexError("a qubit has only output port 0")
        return [self]


class Gate(Element):
    """
    This  is the parent class for all gates in the quantum circuit.
    """
    def __init__(self, sources=None, target=None, qubit_number=1):
        self._qubit_number = qubit_number
        super().__init__(sources=sources, target=target)
        # self._output = None

    # def transformation(self):
        # """
        # This method applies the gate's transformation to the input qubit states and returns the output qubit states.
        # """
        # return self.get_matrix() @ self.combine_entry()

    def get_matrix(self):
        return self._matrix

    # def get_qubit_states(self):
        # return self._output

    # def combine_entry(self):
        # """
        # this method combines the input qubits states into a single state vector for the gate's transformation.
        # """
        # combined_state = np.eye(self._qubit_number * 2)
        # if self.get_sources() is not None:
            # for source in self.get_sources():
                # combined_state = np.kron(combined_state, source.get_qubit_states())
        # return combined_state

    def get_total_delay(self):
        return super().get_total_delay()

    def get_base_matrixes(self):
        """
        This method returns the matrix composition of the gate in the form of 
        M1 ⊗ M2 ⊗... +  M3 ⊗ M4 ⊗... + ..., 
        in the form of
        [[M1, M2, ...], [M3, M4, ...], ...]
        """
        pass

    def get_initial_sources(self, index=None):
        return super().get_initial_sources(index)

    # def refresh_qubits(self):
        # """
        # This method refreshes the qubit states of the gate.
        # """
        # super().refresh_qubits()
        # self._output = self.transformation()


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
        self._qubit_number = qubit_number #this line is here to prevent circular defining
        
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

    # def transformation(self):
        # """
        # This method applies the measurement to the input qubit states and returns the output classical bits.
        # """
        # qubit_states = self.combine_entry()
        # probabilities = np.abs(qubit_states)**2
        # measured_state = np.random.choice(len(probabilities), p=probabilities)
        # output_state = np.zeros_like(qubit_states)
        # output_state[measured_state] = 1
        # return output_state
