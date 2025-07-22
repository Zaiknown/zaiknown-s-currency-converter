# main.py

import tkinter as tk
from app import CurrencyConverterApp

if __name__ == "__main__":
    root = tk.Tk()
    app = CurrencyConverterApp(root)
    app.start()