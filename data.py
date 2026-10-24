import elements
import numpy as np

class Data:
    def __init__(self, element_list):
        self.element_list = element_list
        self.initial_global_state = np.array([1])
        self.delay_list = []
        self.qubit_list = []
        for element in self.element_list:
            if isinstance(element, elements.Qubit):
                self.initial_global_state = np.kron(self.initial_global_state, element.get_qubit_states())
                self.qubit_list.append(element)
            self.delay_list.append(element.get_total_delay())
        self.combined_list = np.array(list(zip(self.element_list, self.delay_list)))
        self.combined_list = self.combined_list[self.combined_list[:, 1].argsort()]

    def get_global_matrix(self, time):
        """
        This method returns the probability matrix of the circuit at a given time.
        """
        #this thing is so ugly I can't believe I wrote it
        #actually it's not that bad, hmm
        self.global_state = self.initial_global_state.copy()
        for element in self.combined_list[self.combined_list[:, 1] <= time][:, 0]:
            if isinstance(element, elements.Gate):
                transformation_matrix_list = []
                for base_matrix in element.get_base_matrixes():
                    transformation_matrix_elements = np.array([[1]])
                    for qubit in self.qubit_list:
                        if qubit in element.get_initial_sources():
                            transformation_matrix_elements = np.kron(transformation_matrix_elements, base_matrix[element.get_initial_sources().index(qubit)])
                        else:
                            transformation_matrix_elements = np.kron(transformation_matrix_elements, np.eye(2))
                    transformation_matrix_list.append(transformation_matrix_elements)
                transformation_matrix = sum(transformation_matrix_list)

                self.global_state = transformation_matrix @ self.global_state
        return self.global_state

    def refresh(self):
        """this method is used to refresh the data layer"""
        self.__init__()