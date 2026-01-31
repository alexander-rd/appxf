'''Manual testing the configuration GUI.'''

from appxf_private.config import Config
from appxf_private.application_gui.config_gui import EditConfigWindow
from appxf_private.gui import KissOption

config = Config()
#config.language['USER'] = 'Benutzer'
#config.language['Cancel'] = 'Abbrechen'
#config.language['OK'] = 'Schließen'

config.add_section('EMPTY')
# Simple string:
config.add_section('USER',
    {'Email': KissOption(type='email'),
     'Rolle': KissOption(type='str'),
     'Ist Admin': KissOption(type='bool'),
     'Irgendein Integer': KissOption(type='int'),
     })
config.section('USER').set('Email', 'empty@email.com')
config.section('USER').set('Rolle', 'Depotbetreuer')
config.section('USER').set('Ist Admin', True)
config.section('USER').set('Irgendein Integer', 15)

gui = EditConfigWindow(config, 'USER')
gui.mainloop()

#config.open_edit_gui('USER', title='Einstellungen für {0}')
#print('..repeat..')
#config.open_edit_gui('USER')

print('DONE')
