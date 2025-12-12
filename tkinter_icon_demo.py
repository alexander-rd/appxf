''' Testing how to properly fit icon buttons next to text buttons. '''
# TODO: The general problem is that the size buttons containing an icon is
# always slightly off compared to buttons containing text.
#
# Motivation is to use much smaller icon buttons in the GUI. This is helpful
# when the action is secondary or there are many actions.

import tkinter as tk
from tkinter import ttk

# Embedded 16x16 PNG icon (base64-encoded); no external dependencies needed.
_SAVE_ICON_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAP0lEQVR42mN4/en/f0owA1UNkHOb"
    "RhTGa4BZ5j68mGgDvn79ioLpbwDFXqDYgBN3/qPgIWjAwAUiRUl5QHIjAGqZM4Zb8Sb4AAAAAElF"
    "TkSuQmCC"
)


def launch():
    """Launch a dummy Tkinter window."""
    root = tk.Tk()
    root.title("KISS CF Tkinter Demo")
    root.geometry("360x220")

    # Render the embedded save icon; keep a reference to prevent GC.
    save_icon = tk.PhotoImage(data=_SAVE_ICON_B64, format="png")

    # Button row inside a framed area for visibility.
    button_frame = tk.Frame(
        root,
        highlightbackground="#8a8a8a",
        highlightthickness=1,
        bd=1,
    )
    button_frame.pack(pady=20)

    style = ttk.Style(root)
    style.configure("Text.TButton", padding=(6, 2))

    # Wrap the icon button in a fixed-size frame so sizing is controlled in pixels.
    save_wrap = tk.Frame(button_frame, width=save_icon.width(), height=save_icon.height())
    save_wrap.pack(side=tk.LEFT, padx=4)
    save_wrap.pack_propagate(False)

    save_button = tk.Button(
        save_wrap,
        image=save_icon,
        command=lambda: None,
        bd=1,
        highlightthickness=0,
        padx=0,
        pady=0,
        relief=tk.RAISED,
    )
    save_button.image = save_icon
    save_button.pack(expand=True, fill=tk.BOTH)

    dummy_button = ttk.Button(
        button_frame, text="dummy", command=lambda: None, style="Text.TButton"
    )
    dummy_button.pack(side=tk.LEFT, padx=4)

    ok_button = ttk.Button(
        button_frame, text="OK", command=lambda: None, style="Text.TButton"
    )
    ok_button.pack(side=tk.LEFT, padx=4)

    def sync_icon_size():
        """Match icon button size to text buttons and keep it square (in pixels)."""
        root.update_idletasks()
        target_h = max(dummy_button.winfo_height(), ok_button.winfo_height())
        side = max(target_h, save_icon.width(), save_icon.height())
        save_wrap.configure(width=side, height=side)
        save_wrap.pack_propagate(False)
        root.update_idletasks()

    root.after_idle(sync_icon_size)

    close_button = tk.Button(root, text="Close", command=root.destroy)
    close_button.pack(pady=10)

    root.mainloop()


if __name__ == "__main__":
    launch()
