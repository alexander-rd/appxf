
# TODO: reactivate storing and loading sections as INI files


class ToolConfigParser(configparser.ConfigParser):
    '''Internal helper with predefined settings for ConfigParser()'''
    def __init__(self):
        # Note that we need to change the comment prefix to something else and
        # allow "no values" to keep them as keys without values. Other
        # functions must then ignore the "#" keys.
        super(ToolConfigParser, self).__init__(
            comment_prefixes='/', allow_no_value=True)
        self.optionxform = str

