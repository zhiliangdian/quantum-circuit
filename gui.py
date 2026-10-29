"""Interactive prototype: drag gates, click output/input ports, inspect states."""
import matplotlib.pyplot as plt
from matplotlib.widgets import Button
from matplotlib.patches import Rectangle, Circle
from matplotlib.lines import Line2D
from matplotlib.backend_bases import MouseButton
import numpy as np
import textwrap
import elements
from data import Model


layout = {
    elements.Qubit: {"input_positions": [], "output_positions": [(1, .5)]},
    elements.Hadamard: {"input_positions": [(0, .5)], "output_positions": [(1, .5)]},
    elements.CNOT: {"input_positions": [(0, .75), (0, .25)], "output_positions": [(1, .75), (1, .25)]},
    elements.Measurement: {"input_positions": [(0, .5)], "output_positions": [(1, .5)]},
    elements.X: {"input_positions": [(0, .5)], "output_positions": [(1, .5)]},
    elements.Z: {"input_positions": [(0, .5)], "output_positions": [(1, .5)]},
}
LABELS = {elements.Hadamard: 'H', elements.CNOT: 'CNOT', elements.Measurement: 'M',
          elements.X: 'X', elements.Z: 'Z'}
STATES = [('0', np.array([1, 0])), ('1', np.array([0, 1])),
          ('+', np.array([1, 1]) / np.sqrt(2)),
          ('+i', np.array([1, 1j]) / np.sqrt(2)),
          ('psi', np.array([np.sqrt(.3), np.sqrt(.7) * np.exp(.7j)]))]


class GUI:
    def __init__(self, show=True):
        self._graphical_data = {}
        self.connections = []  # (Wire, source element, output index, target, input index)
        self._wire_artists = []
        self.selected = None
        self.pending = None
        self.control_source = None
        self.control_mode = False
        self.model = Model([])
        self._main_figure = plt.figure(figsize=(14, 8), facecolor='#f5f7fa')
        self._main_figure.canvas.manager.set_window_title('Quantum circuit prototype')
        self._graphical_figure, self._information_panel = self._main_figure.subfigures(
            1, 2, width_ratios=[2.1, 1])
        self._circuit_figure, self._button_figure = self._graphical_figure.subfigures(
            2, 1, height_ratios=[4, 1])
        self._circuit_figure.set_facecolor('#f5f7fa')
        self._circuit_figure.text(.03, .97, 'CIRCUIT EDITOR', fontsize=14, weight='bold')
        self._circuit_figure.text(.03, .925,
            'Drag bodies. Connect: output dot, then input dot. Right-click a wire to remove it.', fontsize=9)
        self._circuit_figure.text(.03, .885,
            'Time increases left to right. CNOT: top = control, bottom = target.', fontsize=9)
        self._status = self._circuit_figure.text(.03, .035, '', fontsize=9, wrap=True)
        self._information_text = self._information_panel.text(.04, .96, '',
            va='top', fontsize=9, family='monospace', linespacing=1.35)
        self._buttons = []
        actions = [('Qubit', lambda e: self.add_element(elements.Qubit())),
                   ('H', lambda e: self.add_element(elements.Hadamard())),
                   ('CNOT', lambda e: self.add_element(elements.CNOT())),
                   ('Measure', lambda e: self.add_element(elements.Measurement())),
                   ('X', lambda e: self.add_element(elements.X())),
                   ('Z', lambda e: self.add_element(elements.Z())),
                   ('If M=1', self.begin_control), ('Qubit state', self.edit_element),
                   ('Disconnect', self.disconnect_element), ('Delete', self.remove_element),
                   ('New run', self.new_run), ('Teleportation', self.load_teleportation),
                   ('Clear', self.clear), ('Cancel link', self.cancel_link)]
        for index, (label, callback) in enumerate(actions):
            row, col = divmod(index, 7)
            ax = self._button_figure.add_axes([.02 + col * .14, .55 - row * .45, .13, .35])
            button = Button(ax, label, color='#e3eaf2', hovercolor='#c4d9ef')
            button.label.set_fontsize(9)
            button.on_clicked(callback)
            self._buttons.append(button)
        self._main_figure.canvas.mpl_connect('button_press_event', self.on_canvas_press)
        self._main_figure.canvas.mpl_connect('key_press_event', self.on_key)
        self.load_teleportation()
        if show:
            plt.show()

    def message(self, text):
        self._status.set_text(text)
        self._main_figure.canvas.draw_idle()

    def add_element(self, element, position=None, name=None, refresh=True):
        if isinstance(element, elements.Qubit) and sum(isinstance(e, elements.Qubit) for e in self._graphical_data) >= 5:
            self.message('This small demo supports up to five initial qubits.')
            return
        if position is None:
            index = len(self._graphical_data)
            position = (.12 + (index % 6) * .12, .12 + (index % 3) * .2)
        if name is None:
            if isinstance(element, elements.Qubit):
                index = 0
                used = {item['name'].split()[0] for item in self._graphical_data.values()}
                while f'Q{index}' in used:
                    index += 1
                name = f'Q{index}'
            else:
                name = LABELS[type(element)]
        visual = DraggableElement(element, self._circuit_figure, self, position, name)
        self._graphical_data[element] = {'visual': visual, 'position': position, 'name': name}
        if refresh:
            self.changed()
            self.select(element)
        return element

    def connect_element(self, source, output, target, input_port):
        if source is target:
            raise ValueError('Connect two different elements.')
        if self.time_of(source) >= self.time_of(target):
            raise ValueError('Move the target to the right of its source first.')
        if any(s is source and o == output for _, s, o, _, _ in self.connections):
            raise ValueError('That output is already connected. Disconnect its wire first.')
        if any(t is target and i == input_port for _, _, _, t, i in self.connections):
            raise ValueError('That input is already connected. Disconnect its wire first.')
        wire = elements.Wire(sources=source)
        wire.source_port = output
        self.connections.append((wire, source, output, target, input_port))
        return wire

    def port_clicked(self, element, kind, index):
        if self.control_mode:
            self.control_clicked(element)
            return
        if kind == 'output':
            self.pending = (element, index)
            self.message('Output selected. Click an input dot; Esc cancels.')
        elif self.pending is None:
            self.message('Click an output dot first, then this input.')
        else:
            try:
                self.connect_element(*self.pending, element, index)
            except ValueError as error:
                self.message(str(error))
                return
            self.pending = None
            self.changed()
            self.select(element)

    def begin_control(self, event=None):
        self.pending = None
        self.control_mode = True
        self.control_source = None
        self.message('Click a measurement body, then an X or Z body (apply only if its bit is 1).')

    def control_clicked(self, element):
        if self.control_source is None:
            if not isinstance(element, elements.Measurement):
                self.message('Select a measurement first.')
                return
            self.control_source = element
            self.message('Now click the X or Z gate to control.')
            return
        if not isinstance(element, (elements.X, elements.Z)):
            self.message('The correction must be an X or Z gate.')
            return
        if self.time_of(self.control_source) >= self.time_of(element):
            self.message('The correction must be to the right of its measurement.')
            return
        element.condition = self.control_source
        self.cancel_link()
        self.changed()
        self.select(element)

    def cancel_link(self, event=None):
        self.pending = self.control_source = None
        self.control_mode = False
        self.message('Link cancelled. Click a body to inspect; drag it to move.')

    def time_of(self, element):
        if isinstance(element, elements.Qubit):
            return 0.0
        return round(self._graphical_data[element]['visual'].axes.get_position().x0 * 12, 2)

    def changed(self):
        nodes = list(self._graphical_data)
        self.model.set_editor_graph(nodes, self.connections,
                                    {element: self.time_of(element) for element in nodes})
        self.draw_wires()
        self.display_information()

    def draw_wires(self):
        for artist, _ in self._wire_artists:
            artist.remove()
        self._wire_artists = []
        for connection in self.connections:
            wire, source, output, target, input_port = connection
            start = self._graphical_data[source]['visual'].port_position('output', output)
            end = self._graphical_data[target]['visual'].port_position('input', input_port)
            invalid = self.time_of(source) >= self.time_of(target)
            line = Line2D([start[0], end[0]], [start[1], end[1]],
                          transform=self._circuit_figure.transSubfigure,
                          color='#b83232' if invalid else '#45647e', lw=2, picker=6)
            self._circuit_figure.add_artist(line)
            self._wire_artists.append((line, connection))
        for element, item in self._graphical_data.items():
            condition = getattr(element, 'condition', None)
            if condition in self._graphical_data:
                start = self._graphical_data[condition]['visual'].port_position('output', 0)
                end = item['visual'].port_position('input', 0)
                line = Line2D([start[0], end[0]], [start[1] + .02, end[1] + .02],
                              transform=self._circuit_figure.transSubfigure,
                              color='#b47719', linestyle='--', lw=1.5, picker=6)
                self._circuit_figure.add_artist(line)
                self._wire_artists.append((line, element))
        self._main_figure.canvas.draw_idle()

    def on_canvas_press(self, event):
        if any(event.inaxes is item['visual'].axes for item in self._graphical_data.values()):
            return
        for line, connection in reversed(self._wire_artists):
            if line.contains(event)[0]:
                if event.button == MouseButton.RIGHT:
                    if isinstance(connection, tuple):
                        self.connections.remove(connection)
                    else:
                        connection.condition = None
                    self.changed()
                    self.message('Connection removed.')
                elif isinstance(connection, tuple):
                    self.select(connection[0])
                return

    def select(self, element):
        self.selected = element
        for node, item in self._graphical_data.items():
            item['visual'].rectangle.set_edgecolor('#df8e18' if node is element else '#34506b')
            item['visual'].rectangle.set_linewidth(2.5 if node is element else 1)
        self.display_information()

    def validate(self):
        for _, source, _, target, _ in self.connections:
            if self.time_of(source) >= self.time_of(target):
                raise ValueError('A red wire runs backwards in time. Move its target right.')
        for element in self._graphical_data:
            condition = getattr(element, 'condition', None)
            if condition is not None and self.time_of(condition) >= self.time_of(element):
                raise ValueError('Move the conditional X/Z gate after its measurement.')

    @staticmethod
    def vector_text(state):
        if state is None:
            return 'Not available: connect the inputs.'
        state = np.asarray(state).reshape(-1)
        bits = max(1, int(np.log2(len(state))))
        return '\n'.join(f'|{i:0{bits}b}> {value.real:+.3f}{value.imag:+.3f}j'
                         for i, value in enumerate(state) if abs(value) > 1e-8) or 'Zero vector'

    def display_information(self):
        element = self.selected
        if element is None:
            self._information_text.set_text('STATE INSPECTOR\n\nClick an element or wire.\n\nBlue dots: quantum connections\nDashed gold: classical control\n\nQubit state cycles:\n0, 1, +, +i, complex psi\n\nNew run resamples measurement.\nClicking preserves the current run.\n\nLocal states are approximate.\nThey ignore entanglement.\n\nGlobal basis order = initial qubit\ncreation order (Q0, Q1, Q2, ...).')
            return
        name = self._graphical_data[element]['name'] if element in self._graphical_data else 'Wire'
        time = getattr(element, '_editor_time', 0)
        header = f'{name}  |  t = {time:g}\n' + '-' * 35
        try:
            self.validate()
            global_state = self.model.get_global_matrix(time)
            if isinstance(element, elements.Wire):
                element.refresh_qubits()
            local = element.get_qubit_states()
            measurements = ', '.join(f'{self._graphical_data[m]["name"]}={v}'
                                      for m, v in self.model.measurements.items()) or 'none yet'
            basis = ', '.join(self._graphical_data[q]['name'] for q in self.model.qubit_list)
            text = (f'{header}\n\nAPPROXIMATE LOCAL OUTPUT\n(ignores entanglement)\n{self.vector_text(local)}'
                    f'\n\nGLOBAL STATE AFTER t={time:g}\nBasis: {basis}\n{self.vector_text(global_state)}'
                    f'\n\nMeasurement: {measurements}')
            condition = getattr(element, 'condition', None)
            if condition is not None:
                text += f'\nApply if {self._graphical_data[condition]["name"]}=1'
            if isinstance(element, elements.Qubit):
                text += '\n\nUse Qubit state to change input.'
            self._information_text.set_text(text)
            self._information_text.set_fontsize(min(9, max(6, 470 / (1.35 * len(text.splitlines())))))
            self.message('Inspecting this run. New run resamples measurements; edits update the circuit.')
        except (ValueError, IndexError, RecursionError) as error:
            self._information_text.set_text(f'{header}\n\nCircuit incomplete / invalid:\n' + '\n'.join(textwrap.wrap(str(error), 38)))
            self.message('You can keep editing. Connect all inputs before inspecting later times.')
        self._main_figure.canvas.draw_idle()

    def disconnect_element(self, event=None):
        if self.selected is None:
            self.message('Select an element or wire first.')
            return
        selected = self.selected
        self.connections = [c for c in self.connections if selected not in (c[0], c[1], c[3])]
        for element in self._graphical_data:
            if element is selected or getattr(element, 'condition', None) is selected:
                element.condition = None
        if isinstance(selected, elements.Wire):
            self.selected = None
        self.changed()
        self.message('Disconnected. The elements remain available to reconnect.')

    def remove_element(self, event=None):
        selected = self.selected
        if selected is None:
            return
        self.disconnect_element()
        if selected in self._graphical_data:
            self._graphical_data.pop(selected)['visual'].disconnect()
        self.selected = None
        self.pending = self.control_source = None
        self.control_mode = False
        self.changed()

    def edit_element(self, event=None):
        if not isinstance(self.selected, elements.Qubit):
            self.message('Select an initial qubit, then click Qubit state.')
            return
        qubit = self.selected
        qubit._preset = (getattr(qubit, '_preset', 0) + 1) % len(STATES)
        name, state = STATES[qubit._preset]
        qubit.set_qubit_states(self.model, state.copy())
        self.changed()
        self.message(f'Input changed to |{name}>.')

    def new_run(self, event=None):
        self.model.new_run()
        self.display_information()

    def clear(self, event=None):
        for item in self._graphical_data.values():
            item['visual'].disconnect()
        self._graphical_data.clear()
        self.connections.clear()
        self.selected = self.pending = self.control_source = None
        self.control_mode = False
        self.changed()
        self.message('Empty circuit. Add qubits and gates, then connect their dots.')

    def load_teleportation(self, event=None):
        self.clear()
        q0 = self.add_element(elements.Qubit(STATES[4][1].copy()), (.025, .67), 'Q0 psi', False)
        q0._preset = 4
        q1 = self.add_element(elements.Qubit(), (.025, .43), 'Q1 Alice', False)
        q2 = self.add_element(elements.Qubit(), (.025, .19), 'Q2 Bob', False)
        h1 = self.add_element(elements.Hadamard(), (.16, .43), 'H', False)
        bell = self.add_element(elements.CNOT(), (.29, .31), 'CNOT', False)
        cx = self.add_element(elements.CNOT(), (.44, .58), 'CNOT', False)
        h0 = self.add_element(elements.Hadamard(), (.57, .67), 'H', False)
        m0 = self.add_element(elements.Measurement(), (.69, .67), 'M0', False)
        m1 = self.add_element(elements.Measurement(), (.69, .44), 'M1', False)
        x = self.add_element(elements.X(), (.79, .19), 'X', False)
        z = self.add_element(elements.Z(), (.9, .19), 'Z / Bob', False)
        for source, output, target, input_port in [
            (q1, 0, h1, 0), (h1, 0, bell, 0), (q2, 0, bell, 1),
            (q0, 0, cx, 0), (bell, 0, cx, 1), (cx, 0, h0, 0),
            (h0, 0, m0, 0), (cx, 1, m1, 0), (bell, 1, x, 0), (x, 0, z, 0)]:
            self.connect_element(source, output, target, input_port)
        x.condition = m1
        z.condition = m0
        self.changed()
        self.select(z)
        self.message('Editable teleportation example. Try moving gates, removing a wire, or changing Q0.')

    def on_key(self, event):
        if event.key in ('delete', 'backspace'):
            self.remove_element()
        elif event.key == 'escape':
            self.cancel_link()


class DraggableElement:
    """Each element owns an Axes; its body, label and ports move together."""
    def __init__(self, element, figure, gui, position=(.4, .4), name='Gate'):
        self.element, self.figure, self.gui = element, figure, gui
        self.layout = layout[type(element)]
        self._press = None
        self.axes = figure.add_axes([*position, .085, .13])
        self.axes.set(xlim=(-.12, 1.12), ylim=(-.12, 1.12))
        self.axes.set_axis_off()
        self.rectangle = Rectangle((.05, .05), .9, .9, facecolor='#dceafb', edgecolor='#34506b')
        self.axes.add_patch(self.rectangle)
        self.axes.text(.5, .5, name, ha='center', va='center', fontsize=8)
        self.ports = []
        for kind in ('input', 'output'):
            for index, pos in enumerate(self.layout[kind + '_positions']):
                port = Circle(pos, .065, facecolor='#28669a', zorder=4)
                self.axes.add_patch(port)
                self.ports.append((port, kind, index))
        self.canvas = figure.canvas
        self._connections = [self.canvas.mpl_connect(event, callback) for event, callback in (
            ('button_press_event', self.on_press), ('motion_notify_event', self.on_motion),
            ('button_release_event', self.on_release))]

    def port_position(self, kind, index):
        point = self.layout[kind + '_positions'][index]
        return self.figure.transSubfigure.inverted().transform(self.axes.transData.transform(point))

    def on_press(self, event):
        if event.inaxes is not self.axes or self.canvas.widgetlock.locked():
            return
        if event.button == MouseButton.RIGHT:
            self.gui.select(self.element)
            self.gui.disconnect_element()
            return
        if event.button != MouseButton.LEFT:
            return
        if self.gui.control_mode:
            self.gui.control_clicked(self.element)
            return
        for port, kind, index in self.ports:
            if port.contains(event)[0]:
                self.gui.port_clicked(self.element, kind, index)
                return
        if not self.rectangle.contains(event)[0]:
            return
        self.gui.select(self.element)
        self.canvas.widgetlock(self)
        mouse = self.figure.transSubfigure.inverted().transform((event.x, event.y))
        self._press = (self.axes.get_position().bounds, mouse)

    def on_motion(self, event):
        if self._press is None or event.x is None or event.y is None:
            return
        (x, y, width, height), start = self._press
        mouse = self.figure.transSubfigure.inverted().transform((event.x, event.y))
        dx, dy = mouse - start
        self.axes.set_position([np.clip(x + dx, .01, .91), np.clip(y + dy, .1, .72), width, height])
        self.gui.draw_wires()

    def on_release(self, event):
        if self._press is None or event.button != MouseButton.LEFT:
            return
        self._press = None
        self.canvas.widgetlock.release(self)
        self.gui._graphical_data[self.element]['position'] = self.axes.get_position().bounds[:2]
        self.gui.changed()

    def disconnect(self):
        for connection in self._connections:
            self.canvas.mpl_disconnect(connection)
        if self.canvas.widgetlock.isowner(self):
            self.canvas.widgetlock.release(self)
        self.axes.remove()


if __name__ == '__main__':
    GUI()
