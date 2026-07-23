# Task: Fix all bugs in eventlib.py

`eventlib.py` in this directory has SEVERAL subtle bugs. The docstrings are the
authoritative spec - the code must do exactly what they say.

Rules:
- Fix ALL bugs. Do not change the public API (function names, signatures,
  return shapes) or the docstrings' meaning.
- Keep changes minimal and in `eventlib.py` only (you may add your own test
  files for yourself).
- Hidden tests written strictly against the docstrings will grade you.

Python 3.13, stdlib only.
