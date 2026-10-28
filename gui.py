import matplotlib.pyplot as plt
from matplotlib.widgets import Button
import elements

class GUI:
    def __init__(self):
        """
        This is the constructor for the GUI. it is responsible for:
        - initializing the canvas
        - initializing the buttons and other widgets
        - initializing the dictionary that map elements to their graphical data
        """
        self._graphical_data = {}

        #set the canvas in three sections, one for the circuit, one for the buttons and one for the information display
        self._main_canvas = plt.figure(figsize=(10, 10))
        self._graphical_canvas, self._information_panel = self._main_canvas.subfigures(nrows = 1, ncols = 2, width_ratios = [3, 1])
        self._circuit_canvas, self._button_canvas = self._graphical_canvas.subfigures(nrows = 2, ncols = 1, height_ratios = [3, 1])
        self._circuit_canvas = self._circuit_canvas.subplots()
        #add the information text box
        self._information_text = self._information_panel.text(0.5, 0.5, "Information", ha='center', va='center')

        #add the buttons
        button_axes = self._button_canvas.subplots(nrows = 1, ncols = 4)
        self._add_wire = Button(button_axes[0], "Wire")
        self._add_qubit = Button(button_axes[1], "Qubit")
        self._add_Hadamard = Button(button_axes[2], "Hadamard")
        self._add_CNOT = Button(button_axes[3], "CNOT")

        self._add_wire.on_clicked(self.add_element(elements.Wire()))
        self._add_qubit.on_clicked(self.add_element(elements.Qubit()))
        self._add_Hadamard.on_clicked(self.add_element(elements.Hadamard()))
        self._add_CNOT.on_clicked(self.add_element(elements.CNOT()))

        plt.show()


    def add_element(self, element):
        match element:
            case elements.Wire():
                self._graphical_data.append({element: {"start_position": (0, 0), "end_position": (1, 0)}})

            case elements.Qubit():
                self._graphical_data.append({element: {"position": (0, 0), "output_position": (1, 0.5)}})

            case elements.Hadamard():
                self._graphical_data.append({element: {"position": (0, 0), "input_positions": [(0, 0.5)], "output_positions": [(1, 0.5)]}})

            case elements.CNOT():
                self._graphical_data.append({element: {"position": (0, 0), "input_positions": [(0, 0.3), (0, 0.7)], "output_positions": [(1, 0.3), (1, 0.7)]}})

            case _:
                raise ValueError("Unknown element type")

        self.model.add_element(element)
        return None
    
    def remove_element(self):
        pass

    def connect_element(self):
        pass

    def disconnect_element(self):
        pass

    def edit_element(self):
        pass

    def display_information(self):
        pass

    def get_data(self):
        pass

    def handle_user_operation(self):
        pass

GUI()