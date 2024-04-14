import tkinter

from kiss_cf import logging

from kiss_cf.property import KissProperty


class OptionWidget(tkinter.Frame):
    log = logging.getLogger(__name__ + '.ConfigOptionWidget')

    def __init__(self, parent,
                 name: str,
                 option: KissProperty,
                 value: str = '',
                 **kwargs):
        self.log.debug(f'ConfigOptionWidget for {name}: {str(option)}')

        super().__init__(parent, **kwargs)
        # import functoolsself.rowconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        self._name = name
        self._option = option

        self.label = tkinter.Label(self, justify='right')
        self.label.config(text=self._name)
        self.label.grid(row=0, column=0, padx=5, pady=5, sticky='E')

        self.sv = tkinter.StringVar(self, value)
        self.sv.trace_add(
            'write', lambda var, index, mode: self._option_update())

        # TODO: derive width from option (settings)
        self.entry = tkinter.Entry(self, textvariable=self.sv, width=15)
        self.entry.grid(row=0, column=1, padx=5, pady=5, sticky='EW')

        self.is_valid = self._option.validate(self.sv.get())

    def focus_set(self):
        self.entry.focus_set()

    def _option_update(self):
        value = self.sv.get()
        if self._option.validate(value):
            self.is_valid = True
            self.entry.config(foreground='black')
        else:
            self.is_valid = False
            self.entry.config(foreground='red')
