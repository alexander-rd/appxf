'''Provide language helpers.

The language concept is simple: classes that need translations store a user
accessible dictionary and use translate() with this dictionary. If the
dictionary has an entry, the entry is used if not, the key that was looked up
is used.
'''


def translate(language_dict, what):
    '''Get translation from dictionary.'''
    if what in language_dict.keys():
        return language_dict[what]
    else:
        return what
