import os
import sys

# Force Tk to load from bundled location, not system framework
base = sys._MEIPASS

os.environ['TCL_LIBRARY'] = os.path.join(base, 'tcl')
os.environ['TK_LIBRARY'] = os.path.join(base, 'tk')

# tk_path = os.path.join(
#     base,
#     '..',
#     'Frameworks'
# )
#
# os.environ['TK_LIBRARY'] = os.path.join(tk_path, 'tk8.6')
# os.environ['TCL_LIBRARY'] = os.path.join(tk_path, 'tcl8.6')
