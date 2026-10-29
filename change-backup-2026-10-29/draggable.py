"""A draggable Matplotlib rectangle. Run this file for a small demo."""

import matplotlib.pyplot as plt
from matplotlib.backend_bases import MouseButton
from matplotlib.patches import Rectangle


class DraggableElement:
    def __init__(self, container, position=(0, 0), width=0.1, height=0.1):
        """Use data coordinates for Axes, or 0–1 coordinates for a Figure/SubFigure."""
        self.container = container
        if hasattr(container, "transData"):
            self.transform = container.transData
            self.canvas = container.figure.canvas
        else:
            self.transform = container.transSubfigure
            self.canvas = container.canvas
        self.rectangle = Rectangle(position, width, height, facecolor="skyblue",
                                   transform=self.transform)
        container.add_artist(self.rectangle)
        self._press = None
        canvas = self.canvas
        self._connections = [
            canvas.mpl_connect("button_press_event", self.on_press),
            canvas.mpl_connect("motion_notify_event", self.on_motion),
            canvas.mpl_connect("button_release_event", self.on_release),
        ]

    def on_press(self, event):
        if event.button != MouseButton.LEFT:
            return
        canvas = self.canvas
        if canvas.widgetlock.locked() or not self.rectangle.contains(event)[0]:
            return
        canvas.widgetlock(self)
        # Remember both positions so the rectangle does not jump to the cursor.
        mouse_x, mouse_y = self.transform.inverted().transform((event.x, event.y))
        self._press = (self.rectangle.get_xy(), mouse_x, mouse_y)

    def on_motion(self, event):
        if self._press is None:
            return
        (x, y), mouse_x, mouse_y = self._press
        current_x, current_y = self.transform.inverted().transform((event.x, event.y))
        self.rectangle.set_xy((x + current_x - mouse_x,
                               y + current_y - mouse_y))
        self.canvas.draw_idle()

    def on_release(self, event):
        if event.button != MouseButton.LEFT or self._press is None:
            return
        self._press = None
        self.canvas.widgetlock.release(self)

    def disconnect(self):
        canvas = self.canvas
        for connection in self._connections:
            canvas.mpl_disconnect(connection)
        if canvas.widgetlock.isowner(self):
            canvas.widgetlock.release(self)
        self._press = None


if __name__ == "__main__":
    figure = plt.figure()
    figure.suptitle("Click and drag the rectangle")
    # Keep a reference: Matplotlib stores weak references to event handlers.
    draggable = DraggableElement(figure, position=(0.4, 0.4))
    plt.show()
