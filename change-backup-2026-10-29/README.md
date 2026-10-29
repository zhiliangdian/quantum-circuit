# Changes separated on 2026-10-29

The project source has been restored to the user's version immediately before
the assistant's demo fixes (the request to add missing-input guards).
This intentionally preserves unfinished behavior and startup errors.

- `before-*.py`: reconstructed pre-demo versions from the conversation.
- `data.py`, `elements.py`, `gui.py`: complete copies with the demo fixes.
- `assistant-demo.patch`: only the assistant's demo changes, relative to the
  restored source. Checked with `git apply --check`.
- `test.py`, `main.py`, `draggable.py`: additional backup copies, not reverted.

To restore the demo changes from the project root:

```powershell
git apply --check change-backup-2026-10-29/assistant-demo.patch
git apply change-backup-2026-10-29/assistant-demo.patch
```

The earlier standalone `draggable.py` example remains separate and untracked.
No changes were made to the user's `test.py` or tracked Python cache files.
