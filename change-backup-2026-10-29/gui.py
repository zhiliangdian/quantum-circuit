import matplotlib.pyplot as plt
from matplotlib.widgets import Button
from matplotlib.patches import Rectangle, Circle
import elements
from data import Model
from matplotlib.backend_bases import MouseButton

layout = {
    elements.Wire: {"input_positions": [(0.1, 0.5)], "output_positions": [(0.9, 0.5)]},
    elements.Qubit: {"position": (0, 0), "output_positions": [(1, 0.5)]},
    elements.Hadamard: {"input_positions": [(0, 0.5)], "output_positions": [(1, 0.5)]},
    elements.CNOT: {"input_positions": [(0, 0.3), (0, 0.7)], "output_positions": [(1, 0.3), (1, 0.7)]}
}
class GUI:
    def __init__(self):
        """
        This is the constructor for the GUI. it is responsible for:
        - initializing the canvas
        - initializing the buttons and other widgets
        - initializing the dictionary that map elements to their graphical data
        """
        self._graphical_data = {}
        self.model = Model([])

        #set the canvas in three sections, one for the circuit, one for the buttons and one for the information display
        self._main_figure = plt.figure(figsize=(10, 10))
        self._graphical_figure, self._information_panel = self._main_figure.subfigures(nrows = 1, ncols = 2, width_ratios = [3, 1])
        self._circuit_figure, self._button_figure = self._graphical_figure.subfigures(nrows = 2, ncols = 1, height_ratios = [3, 1])
        #add the information text box
        self._information_text = self._information_panel.text(0.5, 0.5, "Information", ha='center', va='center')

        #add the buttons
        button_axes = self._button_figure.subplots(nrows = 1, ncols = 4)
        self._add_wire = Button(button_axes[0], "Wire")
        self._add_qubit = Button(button_axes[1], "Qubit")
        self._add_Hadamard = Button(button_axes[2], "Hadamard")
        self._add_CNOT = Button(button_axes[3], "CNOT")

        self._add_wire.on_clicked(lambda event: self.add_element(elements.Wire()))
        self._add_qubit.on_clicked(lambda event: self.add_element(elements.Qubit()))
        self._add_Hadamard.on_clicked(lambda event: self.add_element(elements.Hadamard()))
        self._add_CNOT.on_clicked(lambda event: self.add_element(elements.CNOT()))

        plt.show()


    def add_element(self, element):
        match element:
            case elements.Wire():
                self._graphical_data[element] = {"start_position": (0, 0), "end_position": (1, 0)}

            case elements.Qubit():
                self._graphical_data[element] = {"position": (0.4, 0.4)}

            case elements.Hadamard():
                self._graphical_data[element] = {"position": (0.4, 0.4)}

            case elements.CNOT():
                self._graphical_data[element] = {"position": (0.4, 0.4)}

            case _:
                raise ValueError("Unknown element type")

        self.model.add_element(element)
        visual = DraggableElement(element, self._circuit_figure)
        self._graphical_data[element]["visual"] = visual
        self._main_figure.canvas.draw_idle()
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


class DraggableElement:
    def __init__(self, element, figure):
        self.element = element
        self.layout = layout[type(element)]
        self._press = None

        self.figure = figure
        self.axes = figure.add_axes([0.4, 0.4, 0.2, 0.2])
        self.axes.set(xlim=(-0.1, 1.1), ylim=(-0.1, 1.1))
        self.axes.set_axis_off()
        self.rectangle = Rectangle((0.1, 0.1), width = 0.8, height = 0.8,
                                   facecolor="skyblue", edgecolor="black")
        self.axes.add_patch(self.rectangle)
        self.axes.text(0.5, 0.5, type(element).__name__, ha="center", va="center")
        self.canvas = self.axes.figure.canvas
        self._connections = [
            self.canvas.mpl_connect("button_press_event", self.on_press),
            self.canvas.mpl_connect("motion_notify_event", self.on_motion),
            self.canvas.mpl_connect("button_release_event", self.on_release),
        ]

        if "input_positions" in self.layout:
            self.input_port = [Circle(pos, radius = 0.05) for pos in self.layout["input_positions"]]
            for port in self.input_port:
                self.axes.add_patch(port)

        if "output_positions" in self.layout:
            self.output_port = [Circle(pos, radius = 0.05) for pos in self.layout["output_positions"]]
            for port in self.output_port:
                self.axes.add_patch(port)

    def on_press(self, event):
        if event.button != MouseButton.LEFT or event.inaxes is not self.axes:
            return
        if self.canvas.widgetlock.locked() or not self.rectangle.contains(event)[0]:
            return

        self.canvas.widgetlock(self)
        mouse = self.figure.transSubfigure.inverted().transform(
            (event.x, event.y)
        )
        self._press = (self.axes.get_position().bounds, mouse)

    def on_motion(self, event):
        if self._press is None:
            return

        (x, y, width, height), mouse_start = self._press
        mouse_now = self.figure.transSubfigure.inverted().transform(
            (event.x, event.y)
        )
        dx, dy = mouse_now - mouse_start

        self.axes.set_position([x + dx, y + dy, width, height])
        self.canvas.draw_idle()

    def on_release(self, event):
        if event.button != MouseButton.LEFT or self._press is None:
            return
        self._press = None
        self.axes.figure.canvas.widgetlock.release(self)

    def disconnect(self):
        canvas = self.axes.figure.canvas
        for connection in self._connections:
            canvas.mpl_disconnect(connection)
        if canvas.widgetlock.isowner(self):
            canvas.widgetlock.release(self)
        self._press = None

if __name__ == "__main__":
    GUI()
