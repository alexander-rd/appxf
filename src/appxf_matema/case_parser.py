
import inspect


class CaseParser:
    def __init__(self, frame_index):
        stack = inspect.stack()
        caller_frame = stack[frame_index]

        self.module = inspect.getmodule(caller_frame[0])

        if self.module:
            self.caller_module_name = self.module.__name__
            self.caller_module_path = self.module.__file__ or 'Unknown'
            self.caller_module_docstring = (
                self.module.__doc__ or 'No docstring')

            # Extract all defined functions (not imported)
            self.caller_module_functions = []
            self.caller_module_function_map = {}
            for name, obj in inspect.getmembers(self.module):
                if (inspect.isfunction(obj)
                        and obj.__module__ == self.module.__name__):
                    self.caller_module_functions.append(name)
                    # Extract first paragraph (summary) of docstring
                    # per PEP 257
                    docstring = obj.__doc__ or ''
                    # Get text before first blank line (or entire docstring
                    # if no blank line)
                    parts = docstring.split('\n\n')
                    summary = parts[0].strip()
                    # Collapse multi-line summary into single line
                    summary = ' '.join(summary.split())
                    self.caller_module_function_map[name] = summary
        else:
            self.caller_module_name = ''
            self.caller_module_path = ''
            self.caller_module_docstring = ''
            self.caller_module_functions = []
            self.caller_module_function_map = {}

        self.report()

    def report(self):
        print(
            f'CaseParser identified module: {self.caller_module_name}\n'
            f'path: {self.caller_module_path}\n'
            f'functions: {self.caller_module_functions}\n'
            f'as map: {self.caller_module_function_map}\n'
            f'docstring: {self.caller_module_docstring}'
        )
