import matplotlib.pyplot as plt
from matplotlib.widgets import Button
from matplotlib.patches import Rectangle, Circle, ConnectionPatch
import elements
from matplotlib.backend_bases import MouseButton
from data import Model

class WireInput():
    """
    this is a placeholder for identifying the input of a wire.
    """
    def __init__(self, wire):
        self.wire = wire

    def set_source(self, source):
        self.wire.set_source(source)

class WireOutput():
    """
    this is a placeholder for identifying the output of a wire.
    """
    def __init__(self, wire):
        self.wire = wire

    def set_target(self, target):
        self.wire.set_target(target)

layout = {
    WireInput: {"input_positions": [(0.4, 0.4)]},
    WireOutput: {"output_positions": [(0.4, 0.4)]},
    elements.Qubit: {"output_positions": [(0.95, 0.5)]},
    elements.Hadamard: {"input_positions": [(0.05, 0.5)], "output_positions": [(0.95, 0.5)]},
    elements.CNOT: {"input_positions": [(0.05, 0.3), (0.05, 0.7)], "output_positions": [(0.95, 0.3), (0.95, 0.7)]}
}
class GUI:
    def __init__(self, show=True):
        """
        This is the constructor for the GUI. it is responsible for:
        - initializing the canvas
        - initializing the buttons and other widgets
        - initializing the dictionary that map elements to their graphical data
        """
        self._graphical_data = {}
        self.model = Model()

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

        if show:
            plt.show()


    def add_element(self, element):
        match type(element):
            case elements.Wire:
                self._graphical_data[element] = {"start_position": (0, 0), "end_position": (1, 0)}
                self._graphical_data[element]["draggablepointers"] = DraggableWire(element, self._circuit_figure, model = self.model) 
                self.model.add_element(element)
                self._main_figure.canvas.draw_idle()
                return

            case elements.Qubit:
                self._graphical_data[element] = {"position": (0.4, 0.4)}

            case elements.Hadamard:
                self._graphical_data[element] = {"position": (0.4, 0.4)}

            case elements.CNOT:
                self._graphical_data[element] = {"position": (0.4, 0.4)}

            case _:
                raise ValueError("Unknown element type")

        self.model.add_element(element)
        self._graphical_data[element]["draggable"] = DraggableElement(element, self._circuit_figure, model = self.model)
        self._main_figure.canvas.draw_idle()
    
    def remove_element(self):
        pass
    


class DraggableElement:
    def __init__(self, element, figure, size=(0.1, 0.1), position=(0.4, 0.4), port_size=0.07, model= None):
        self.model = model
        self.element = element
        self.layout = layout[type(element)]
        self._press = None

        self.figure = figure
        self.figure.subplots_adjust(left=0, right=1, top=1, bottom=0)
        self.axes = self.figure.add_axes ([position[0], position[1], size[0], size[1]])
        self.axes.axis('off')
        self.axes.set_aspect("equal", adjustable="box")
        self.rectangle = Rectangle((0.05, 0.05), width = 0.9, height = 0.9)
        self.rectangle.set_facecolor("white")
        self.rectangle.set_edgecolor("black")
        self.axes.add_patch(self.rectangle)
        self.canvas = self.axes.figure.canvas
        self._connections = [
            self.canvas.mpl_connect("button_press_event", self.on_press),
            self.canvas.mpl_connect("motion_notify_event", self.on_motion),
            self.canvas.mpl_connect("button_release_event", self.on_release),
        ]

        self.textbox = self.axes.text(0.5, 0.5, type(element).__name__, ha='center', va='center', fontsize=12)

        if "input_positions" in self.layout:
            self.input_port = [Circle(pos, radius = port_size, gid = "input") for pos in self.layout["input_positions"]]
            for port in self.input_port:
                port.set_facecolor("black")
                self.axes.add_patch(port)
                port.owner = self
                port.connected = False

        if "output_positions" in self.layout:
            self.output_port = [Circle(pos, radius = port_size, gid = "output" ) for pos in self.layout["output_positions"]]
            for port in self.output_port:
                port.set_facecolor("black")
                self.axes.add_patch(port)
                port.owner = self
                port.connected = False

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

        #disconnect all ports
        if hasattr(self, "input_port"):
            self.model.disconnect_source(self.get_element(), refresh=False)
        if hasattr(self, "output_port"):
            self.model.disconnect_target(self.get_element(), refresh=False)

        #set the connection between elements
        #if statement pyramid :(
        for ports in getattr(self, "input_port", []):
            for other_ports in self.figure.findobj(match = Circle):
                if other_ports is not ports and ports.get_extents().overlaps(other_ports.get_extents()):
                    if other_ports.get_gid() == "output":
                        source = other_ports.owner.get_element()
                        target = self.get_element()
                        if source is target:
                            continue
                        self.model.connect_elements(source, target, other_ports.owner.output_port.index(other_ports), self.input_port.index(ports), refresh=False)
                        ports.connected = True
                        other_ports.connected = True

        for ports in getattr(self, "output_port", []):
            for other_ports in self.figure.findobj(match = Circle):
                if other_ports is not ports and ports.get_extents().overlaps(other_ports.get_extents()):
                    if other_ports.get_gid() == "input":
                        source = self.get_element()
                        target = other_ports.owner.get_element()
                        if source is target:
                            continue
                        self.model.connect_elements(source, target, self.output_port.index(ports), other_ports.owner.input_port.index(other_ports), refresh=False)
                        ports.connected = True
                        other_ports.connected = True

        self.model.refresh()
        # Derive visual flags from the final connections, including old partners.
        for port in self.figure.findobj(match=Circle):
            owner = getattr(port, "owner", None)
            if owner is None:
                continue
            element = owner.get_element()
            if port.get_gid() == "input":
                port.connected = element.get_sources()[owner.input_port.index(port)] is not None
            elif port.get_gid() == "output":
                port.connected = element.get_target()[owner.output_port.index(port)] is not None

    def disconnect(self):
        canvas = self.axes.figure.canvas
        for connection in self._connections:
            canvas.mpl_disconnect(connection)
        if canvas.widgetlock.isowner(self):
            canvas.widgetlock.release(self)
        self._press = None

    def set_text(self, text):
        """
        this method set the text displayed on the element.
        """
        self.textbox.set_text(text)

    def get_element(self):
        """
        this method returns the element associated with this draggable element.
        """
        if type(self.element) in [WireInput, WireOutput]:
            return self.element.wire
        return self.element



class DraggableWire():
    def __init__(self, wire, figure, model = None):
        self.wire = wire
        self.figure = figure
        self.model = model
        input_pos = [0.35, 0.5]
        output_pos = [0.6, 0.5]
        self.input_point = DraggableElement(WireInput(wire), figure, size = [0.01, 0.01], position = input_pos, port_size = 0.5, model = model)
        self.output_point = DraggableElement(WireOutput(wire), figure, size = [0.01, 0.01], position = output_pos, port_size = 0.5, model = model)
        self.output_point.rectangle.set_visible(False)
        self.input_point.rectangle.set_visible(False)
        self.input_point.set_text("In")
        self.output_point.set_text("Out")
        # Each endpoint uses its own axes transform, so it follows dragging
        # and resizing without an extra axes covering the circuit.
        self.line = ConnectionPatch(
            xyA=self.input_point.layout["input_positions"][0],
            coordsA=self.input_point.axes.transData,
            xyB=self.output_point.layout["output_positions"][0],
            coordsB=self.output_point.axes.transData,
            color="black", linewidth=2, clip_on=False,
        )
        self.figure.add_artist(self.line)

    def disconnect(self):
        self.input_point.disconnect()
        self.output_point.disconnect()




if __name__ == "__main__":
    GUI()
