"""Headless checks: python -m unittest test_gui_demo -v."""
import unittest
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backend_bases import MouseEvent
import numpy as np
import elements
from gui import GUI, STATES


class EditorDemoTests(unittest.TestCase):
    def setUp(self):
        self.app = GUI(show=False)

    def tearDown(self):
        plt.close('all')

    def test_teleportation_all_outcomes_and_complex_inputs(self):
        app = self.app
        initial = app.model.qubit_list[0]
        observed = set()
        for _, vector in STATES:
            initial.set_qubit_states(app.model, vector)
            for seed in range(16):
                app.model.seed = seed
                state = app.model.get_global_matrix(100).reshape(4, 2)
                bob = state.conj().T @ state
                # Our row convention makes rho the conjugate of this product.
                self.assertTrue(np.allclose(bob.conj(), np.outer(vector, vector.conj())))
                observed.add(tuple(app.model.measurements.values()))
                self.assertAlmostEqual(np.linalg.norm(state), 1)
        self.assertEqual(observed, {(0, 0), (0, 1), (1, 0), (1, 1)})

    def test_time_and_measurement_stability(self):
        model = self.app.model
        final = model.get_global_matrix(100)
        results = model.measurements.copy()
        start = model.get_global_matrix(0)
        self.assertTrue(np.allclose(start, model.initial_global_state))
        self.assertEqual(model.measurements, {})
        self.assertTrue(np.allclose(final, model.get_global_matrix(100)))
        self.assertEqual(results, model.measurements)

    def test_disconnect_reconnect_and_branch_rejection(self):
        app = self.app
        wire, source, output, target, port = app.connections[0]
        app.selected = wire
        app.disconnect_element()
        with self.assertRaisesRegex(ValueError, 'connect every input'):
            app.model.get_global_matrix(100)
        app.connect_element(source, output, target, port)
        app.changed()
        self.assertAlmostEqual(np.linalg.norm(app.model.get_global_matrix(100)), 1)
        with self.assertRaisesRegex(ValueError, 'already connected'):
            app.connect_element(source, output, target, port)

    def test_drag_and_port_clicks(self):
        app = self.app
        app.clear()
        source = app.add_element(elements.Qubit(), (.1, .4))
        target = app.add_element(elements.Hadamard(), (.5, .4))
        canvas = app._main_figure.canvas
        canvas.draw()
        def mouse(name, point, button=1):
            canvas.callbacks.process(name, MouseEvent(name, canvas, *point, button=button))
        for element, kind in [(source, 'output'), (target, 'input')]:
            visual = app._graphical_data[element]['visual']
            point = app._circuit_figure.transSubfigure.transform(visual.port_position(kind, 0))
            mouse('button_press_event', point)
            mouse('button_release_event', point)
        self.assertEqual(len(app.connections), 1)
        visual = app._graphical_data[target]['visual']
        start = visual.axes.transData.transform((.5, .5))
        old = visual.axes.get_position().bounds
        mouse('button_press_event', start)
        mouse('motion_notify_event', start + np.array([30, 20]))
        mouse('button_release_event', (1, 1))
        self.assertNotEqual(old, visual.axes.get_position().bounds)
        self.assertFalse(canvas.widgetlock.locked())
        self.assertTrue(np.allclose(app.model.get_global_matrix(100), [2**-.5, 2**-.5]))

    def test_delete_and_invalid_time(self):
        app = self.app
        final = app.selected
        visual = app._graphical_data[final]['visual']
        visual.axes.set_position([.01, .2, .085, .13])
        app.changed()
        with self.assertRaises(ValueError):
            app.validate()
        self.assertIn('invalid', app._information_text.get_text())
        app.remove_element()
        self.assertNotIn(final, app._graphical_data)
        self.assertTrue(all(final not in (c[1], c[3]) for c in app.connections))
        app.clear()
        self.assertEqual(len(app.model.element_list), 0)


if __name__ == '__main__':
    unittest.main()
