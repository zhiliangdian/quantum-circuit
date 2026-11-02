"""Headless regression checks for GUI buttons and wire dragging."""
import unittest

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backend_bases import MouseButton, MouseEvent
import numpy as np

import gui


class GUITest(unittest.TestCase):
    def setUp(self):
        self.app = gui.GUI(show=False)
        self.canvas = self.app._main_figure.canvas
        self.canvas.draw()

    def tearDown(self):
        plt.close("all")

    def mouse(self, name, xy):
        event = MouseEvent(name, self.canvas, *xy, button=MouseButton.LEFT)
        self.canvas.callbacks.process(name, event)

    def click(self, button):
        xy = button.ax.transAxes.transform((0.5, 0.5))
        self.mouse("button_press_event", xy)
        self.mouse("button_release_event", xy)

    def test_buttons_add_distinct_model_and_graphical_elements(self):
        self.assertEqual(len(self.app.model.element_list), 0)
        for button in (self.app._add_wire, self.app._add_qubit,
                       self.app._add_Hadamard, self.app._add_CNOT,
                       self.app._add_wire, self.app._add_Hadamard):
            self.click(button)
        self.assertEqual(len(self.app.model.element_list), 6)
        self.assertEqual(len(self.app._graphical_data), 6)
        self.assertEqual(len(self.app.model.qubit_list), 1)

    def assert_line_attached(self, wire):
        self.canvas.draw()
        vertices = wire.line.get_transform().transform(wire.line.get_path().vertices)
        np.testing.assert_allclose(vertices[0], wire.input_point.axes.transData.transform(
            wire.input_point.layout["input_positions"][0]))
        np.testing.assert_allclose(vertices[-1], wire.output_point.axes.transData.transform(
            wire.output_point.layout["output_positions"][0]))

    def test_wire_endpoints_drag_independently_and_follow_resize(self):
        self.click(self.app._add_wire)
        wire = next(iter(self.app._graphical_data.values()))["draggablepointers"]
        self.assert_line_attached(wire)
        for point, other in ((wire.input_point, wire.output_point),
                             (wire.output_point, wire.input_point)):
            before = np.array(point.axes.get_position().bounds)
            other_before = other.axes.get_position().bounds
            xy = point.axes.transData.transform((0.5, 0.5))
            self.mouse("button_press_event", xy)
            self.assertTrue(self.canvas.widgetlock.isowner(point))
            self.mouse("motion_notify_event", xy + (30, -25))
            self.mouse("button_release_event", xy + (30, -25))
            self.assertFalse(self.canvas.widgetlock.locked())
            self.assertFalse(np.allclose(before[:2], point.axes.get_position().bounds[:2]))
            np.testing.assert_allclose(other_before, other.axes.get_position().bounds)
            self.assert_line_attached(wire)
        self.app._main_figure.set_size_inches(12, 8)
        self.assert_line_attached(wire)
        wire.disconnect()
        xy = wire.input_point.axes.transData.transform((0.5, 0.5))
        self.mouse("button_press_event", xy)
        self.assertFalse(self.canvas.widgetlock.locked())


if __name__ == "__main__":
    unittest.main()
