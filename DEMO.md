# Circuit editor demo

Run `python main.py` with NumPy and Matplotlib installed. `python gui.py` also
works. An editable teleportation circuit is loaded at startup.

## Controls

- Drag an element's body to move it. Its ports and wires follow.
- Click a blue output dot, then a blue input dot to connect them.
- Right-click a wire to remove it. Click a wire to inspect it.
- Click a body to inspect its output and the global vector at that time.
- Right-click a body, or select it and use **Disconnect**, to remove its links.
- **Delete** removes the selected element or wire. Delete/Backspace also works.
- **If M=1**: click a measurement, then an X/Z gate to add classical control.
  The dashed gold line is classical, not a second quantum wire. Right-click
  that line to remove the condition (the gate then runs unconditionally).
- **Qubit state** cycles the selected initial qubit through 0, 1, +, +i and a
  complex example. Its exact amplitudes appear in the inspector.
- **New run** resamples measurements. Clicking around preserves the run's
  outcomes. The same result can occur again on a new run.
- **Clear** starts an empty circuit. **Teleportation** replaces the circuit
  with the example. These two buttons discard the current layout.
- Escape or **Cancel link** cancels a pending quantum/classical link.

Time increases with the horizontal position of gates. Initial qubits exist
at time zero regardless of where they are drawn. All connected gates must be
to the right of their upstream gates. A backwards connection is shown red
and inspection explains what needs fixing. The global vector includes gates
at the selected time, not just those on the selected wire. Incomplete circuits
can be edited but cannot be simulated beyond an unconnected gate.

The CNOT's upper port is control, lower port is target; output order is the same.
A quantum output has at most one outgoing wire. Multiple classical controls
can use the same measurement bit. This small demo limits input qubits to five.

## A short walkthrough

1. Click Q0 and show its complex input vector.
2. Click the first CNOT. The global state now contains the Bell pair.
3. Click M0 or M1 and show the sampled measurement bits.
4. Click the final Z / Bob gate. Read the two nonzero global amplitudes:
   the first two basis bits are Alice's outcomes, and Bob's final bit has
   Q0's original amplitudes. Both conditional corrections are necessary in
   general; an individual run may not need both.
5. Use New run to try another outcome. Drag a gate, remove a wire, and reconnect
   it to demonstrate that this is an editable graph rather than an animation.

The correction rule is X when M1=1, followed by Z when M0=1. Protocol reference:
[IBM Quantum's teleportation explanation](https://quantum.cloud.ibm.com/learning/en/courses/utility-scale-quantum-computing/teleportation).

## Prototype limitations and code changes

**The local output is intentionally approximate.** Gates still calculate from
the tensor product of their local inputs. When a multi-qubit output is split
into wires, each wire sums amplitudes over the other ports and normalizes; if
that cancels to zero it uses the largest column. This is a crude approximation,
not a physically valid reduced state for an entangled subsystem. It may differ
from Bob's actual state even when the global teleportation result is correct.
The inspector labels it accordingly. No density-matrix UI was added.

Your pre-demo checkpoint is commit `35f118f`. The additions after it are:

- `gui.py`: completed editor interactions around GUI/DraggableElement and the
  figure/subfigure layout; ports, wires, inspector, buttons, and the example.
- `elements.py`: missing-input guards, identity-based mutable elements, wire
  output-port selection/approximation, and X/Z gates. Removed import-time demo.
- `data.py`: kept Model and get_global_matrix(time); fixed empty/refresh handling,
  added topology updates and ordered gate application on the global vector,
  plus measurement and classical conditions. It applies gate matrices to the
  connected qubit indices rather than tensoring independent local outputs.
- `main.py`, `logic_and_computation.py`, and your original `test.py` are unchanged.

These GUI/backend completions were assistant additions to the existing
prototype. The checkpoint makes it possible to review or discuss them separately
from the earlier implementation. Nothing has been committed over that checkpoint.

Verification: `python -m unittest test_gui_demo -v` uses a headless Matplotlib
backend and checks graph edits, mouse events, time inspection, stable measurement,
and global teleportation for all four outcomes and several input states.
