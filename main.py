import sys
import os

# Ensure the project root is always on the Python path regardless of how
# the script is invoked.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tkinter as tk
from gui.app import App


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == '__main__':
    main()
