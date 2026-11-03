import elements
import numpy as np

class Model:
    def __init__(self, element_list=None):
        self.element_list = list(element_list) if element_list is not None else []
        self.initial_global_state = np.array([1])
        self.delay_list = []
        self.qubit_list = []
        for element in self.element_list:
            if isinstance(element, elements.Qubit):
                self.initial_global_state = np.kron(self.initial_global_state, element.get_qubit_states())
                self.qubit_list.append(element)
            self.delay_list.append(element.get_total_delay())


    def get_global_matrix(self, time):
        """
        This method returns the probability matrix of the circuit at a given time.
        """
        #this method need to be optimized to be generating a lookup table for each time step, instead of calculating the global state from scratch every time.

        #this thing is so ugly I can't believe I wrote it
        #actually it's not that bad, hmm
        #no it's still UGLYYYYYY
        self.global_state = self.initial_global_state.copy()
        ready = set(self.qubit_list)
        for element in self.combined_list[self.combined_list[:, 1] <= time][:, 0]:
            if isinstance(element, elements.Qubit):
                continue
            if any(connection is None or connection[0] not in ready
                   for connection in element.get_sources()):
                continue
            if isinstance(element, elements.Gate):
                initial_sources = element.get_initial_sources()
                transformation_matrix_list = []
                
                for base_matrix in element.get_base_matrixes():
                    transformation_matrix_elements = np.array([[1]])

                    for qubit in self.qubit_list:
                        if qubit in initial_sources:
                            transformation_matrix_elements = np.kron(transformation_matrix_elements, base_matrix[initial_sources.index(qubit)])
                        else:
                            #tensoring with identity matrix for qubits not involved in the gate
                            transformation_matrix_elements = np.kron(transformation_matrix_elements, np.eye(2))
                    transformation_matrix_list.append(transformation_matrix_elements)
                transformation_matrix = sum(transformation_matrix_list)

                self.global_state = transformation_matrix @ self.global_state
            ready.add(element)
        return self.global_state

    def refresh(self):
        """this method is used to refresh the data layer"""
        self.__init__(self.element_list)
        # Keep upstream gates first even when their delays are equal.
        ordered = []
        visited = set()

        def visit(element):
            if element in visited:
                return
            visited.add(element)
            if isinstance(element, elements.Element):
                for connection in element.get_sources():
                    if connection is not None:
                        visit(connection[0])
            ordered.append(element)

        for element in self.element_list:
            visit(element)
        self.combined_list = np.array(
            [(element, element.get_total_delay()) for element in ordered],
            dtype=object).reshape(-1, 2)
        #sort the combined list based on delay time
        self.combined_list = self.combined_list[np.argsort(self.combined_list[:, 1], kind="stable")]
        # for element in self.element_list:
        #     if isinstance(element, elements.Element):
        #         element.refresh_qubits()

    def add_element(self, element):
        self.element_list.append(element)
        self.refresh()

    def connect_elements(self, source, target, source_index, target_index, refresh=True):
        if not 0 <= source_index < len(source.get_target()):
            raise IndexError("invalid output port")
        if not 0 <= target_index < len(target.get_sources()):
            raise IndexError("invalid input port")
        # A feedback connection would make delay and qubit tracing recurse forever.
        pending, visited = [source], set()
        while pending:
            element = pending.pop()
            if element is target:
                raise ValueError("a circuit connection cannot create a cycle")
            if element in visited:
                continue
            visited.add(element)
            if isinstance(element, elements.Element):
                pending.extend(connection[0] for connection in element.get_sources()
                               if connection is not None)
        self.disconnect_target(source, source_index, refresh=False)
        self.disconnect_source(target, target_index, refresh=False)
        source.set_target(self, (target, target_index), index=source_index)
        target.set_sources(self, (source, source_index), index=target_index)
        if refresh:
            self.refresh()

    def disconnect_source(self, element, index=None, refresh=True):
        indices = range(len(element.get_sources())) if index is None else [index]
        for target_index in indices:
            connection = element.get_sources()[target_index]
            if connection is None:
                continue
            source, source_index = connection
            source.set_target(self, None, index=source_index)
            element.set_sources(self, None, index=target_index)
        if refresh:
            self.refresh()

    def disconnect_target(self, element, index=None, refresh=True):
        indices = range(len(element.get_target())) if index is None else [index]
        for source_index in indices:
            connection = element.get_target()[source_index]
            if connection is None:
                continue
            target, target_index = connection
            target.set_sources(self, None, index=target_index)
            element.set_target(self, None, index=source_index)
        if refresh:
            self.refresh()
        
