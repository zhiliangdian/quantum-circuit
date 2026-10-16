from dataclasses import dataclass
from data import Data

@dataclass(frozen=True)
class element:
    def __init__(self, qubit_states, source = None, target = None):
        self.set_qubit_states(qubit_states)
        self.set_source(source)
        self.set_target(target)

    def get_qubit_states(self):
        return self.__qubit_states

    @property
    def get_source(self):
        return self.__source

    def get_target(self):
        return self.__target

    def set_qubit_states(self, editor, new_states):
        if type(editor) in [Data, element]:
            self.__qubit_states = new_states
        else:
            raise ValueError("data in elements must be edited from data layer")
    
    @property
    def set_source(self, editor, new_source):
        if type(editor) in [Data, element]:
            self.__source = new_source
        else:
            raise ValueError("data in elements must be edited from data layer")

    def set_target(self, editor, new_target):
        if type(editor) in [Data, element]:
            self.__target = new_target
        else:
            raise ValueError("data in elements must be edited from data layer")


class Wire(element):
    def __init__(self, qubit_states, source=None, target=None):
        super().__init__(qubit_states, source, target)

class Qubit(element):
    def __init__(self, qubit_states, target=None):
        super().__init__(qubit_states, target = target)

    @property
    def set_source(self, editor, new_source):
        raise ValueError("qubits cannot have a source.")

class Gate(element):
    def __init__(self, qubit_states, source=None, target=None):
        super().__init__(qubit_states, source, target)
    