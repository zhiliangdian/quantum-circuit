"""A draggable Matplotlib rectangle. Run this file for a small demo."""

import matplotlib.pyplot as plt
from matplotlib.backend_bases import MouseButton
from matplotlib.patches import Rectangle


class DraggableElement:
    def __init__(self, axes, position=(0, 0), width=1, height=1):
        self.axes = axes
        self.rectangle = Rectangle(position, width, height, facecolor="skyblue")
        axes.add_patch(self.rectangle)
        self._press = None
        canvas = axes.figure.canvas
        self._connections = [
            canvas.mpl_connect("button_press_event", self.on_press),
            canvas.mpl_connect("motion_notify_event", self.on_motion),
            canvas.mpl_connect("button_release_event", self.on_release),
        ]

    def on_press(self, event):
        if event.button != MouseButton.LEFT or event.inaxes is not self.axes:
            return
        canvas = self.axes.figure.canvas
        if canvas.widgetlock.locked() or not self.rectangle.contains(event)[0]:
            return
        canvas.widgetlock(self)
        # Remember both positions so the rectangle does not jump to the cursor.
        self._press = (self.rectangle.get_xy(), event.xdata, event.ydata)

    def on_motion(self, event):
        if self._press is None or event.inaxes is not self.axes:
            return
        (x, y), mouse_x, mouse_y = self._press
        self.rectangle.set_xy((x + event.xdata - mouse_x,
                               y + event.ydata - mouse_y))
        self.axes.figure.canvas.draw_idle()

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
    figure, axes = plt.subplots()
    axes.set(xlim=(0, 10), ylim=(0, 10), aspect="equal",
             title="Click and drag the rectangle")
    # Keep a reference: Matplotlib stores weak references to event handlers.
    draggable = DraggableElement(axes, position=(4, 4))
    plt.show()
