import elements
import numpy as np


class Model:
    """Elements ordered by time; local outputs retain the prototype calculation."""

    def __init__(self, element_list):
        self.element_list = element_list
        self.seed = 0
        self.measurements = {}
        self.refresh()

    def refresh(self):
        self.qubit_list = [e for e in self.element_list if isinstance(e, elements.Qubit)]
        self.initial_global_state = np.array([1.0 + 0j])
        for qubit in self.qubit_list:
            state = np.asarray(qubit.get_qubit_states(), dtype=complex).reshape(-1)
            if state.size != 2 or not np.isclose(np.linalg.norm(state), 1):
                raise ValueError("Each initial qubit needs a normalized two-entry vector.")
            self.initial_global_state = np.kron(self.initial_global_state, state)
        self.delay_list = [getattr(e, '_editor_time', None) for e in self.element_list]
        self.delay_list = [e.get_total_delay() if t is None else t
                           for e, t in zip(self.element_list, self.delay_list)]
        self.combined_list = np.array(list(zip(self.element_list, self.delay_list)),
                                      dtype=object).reshape(-1, 2)
        self.combined_list = self.combined_list[self.combined_list[:, 1].argsort(kind='stable')]

    def add_element(self, element):
        self.element_list.append(element)
        self.refresh()

    def set_editor_graph(self, nodes, connections, times):
        """Apply the GUI's port connections in the data layer."""
        for element in nodes:
            element._editor_time = times[element]
            if isinstance(element, elements.Gate):
                element._sources = [None] * element._qubit_number
                element._output = None
        for wire, source, output, target, input_port in connections:
            wire._sources = source
            wire._target = target
            wire.source_port = output
            wire._delay = times[target] - times[source]
            wire._editor_time = times[target]
            target._sources[input_port] = wire
        self.element_list = nodes + [c[0] for c in connections]
        self.refresh()

    def get_global_matrix(self, time):
        """State after gates at or before time, in initial-qubit creation order.

        A fixed seed keeps measurement results stable while inspecting a run.
        Local gate outputs use tensor products as in the original prototype;
        port-specific wires discard correlations for the local display only.
        """
        self.refresh()
        self.global_state = self.initial_global_state.copy()
        self.measurements = {}
        rng = np.random.default_rng(self.seed)
        count = len(self.qubit_list)
        for element, gate_time in self.combined_list:
            if gate_time > time or not isinstance(element, elements.Gate):
                continue
            sources = element.get_sources()
            if sources is None or len(sources) != element._qubit_number or any(s is None for s in sources):
                raise ValueError(f"{type(element).__name__} at t={gate_time:g}: connect every input.")
            roots = element.get_initial_sources()
            if len(roots) != element._qubit_number or len(set(roots)) != len(roots):
                raise ValueError("A gate needs distinct connected qubits at its inputs.")
            indices = [self.qubit_list.index(q) for q in roots]
            for source in sources:
                if isinstance(source, elements.Wire):
                    source.refresh_qubits()
            condition = getattr(element, 'condition', None)
            if condition is not None and condition not in self.measurements:
                raise ValueError("The controlling measurement must be earlier than its X/Z gate.")
            order = indices + [i for i in range(count) if i not in indices]
            rows = self.global_state.reshape([2] * count).transpose(order).reshape(2 ** len(indices), -1)
            if isinstance(element, elements.Measurement):
                probabilities = np.sum(np.abs(rows) ** 2, axis=1)
                result = int(rng.choice(len(probabilities), p=probabilities / probabilities.sum()))
                rows = rows.copy()
                rows[np.arange(len(rows)) != result] = 0
                rows /= np.sqrt(probabilities[result])
                self.measurements[element] = result
                element._output = np.eye(len(rows))[result]
            elif condition is None or self.measurements[condition] == 1:
                rows = element.get_matrix() @ rows
                element.refresh_qubits()
            else:
                element._output = element.combine_entry()
            self.global_state = rows.reshape([2] * count).transpose(np.argsort(order)).reshape(-1)
        return self.global_state.copy()

    def new_run(self):
        self.seed += 1
