'''Manual testing the configuration GUI.'''

# Run via: python -m ooTool.test.test_config_gui

from ..config import Config

config = Config()
config.language['USER'] = 'Benutzer'
config.language['Cancel'] = 'Abbrechen'
config.language['OK'] = 'Schließen'

config.add_section('EMPTY')
# Simple string:
config.add_option('USER', 'Email', value='empty@email.com')
# Preselection:
config.add_option('USER', 'Rolle', value='Depotbetreuer')
# Boolean:
config.add_option('USER', 'Ist Admin', value='True')
# Integer:
config.add_option('USER', 'Irgendein Integer', value='15')

#config.keyConfig('USER', 'email')

config.open_edit_gui('USER', title='Einstellungen für {0}')
print('..repeat..')
config.open_edit_gui('USER')

print('DONE')