# Copyright 2023-2026 the contributors of APPXF (github.com/alexander-nbg/appxf)
# SPDX-License-Identifier: Apache-2.0
"""Manual testing the configuration GUI."""

from appxf.application_gui.config_gui import EditConfigWindow

from appxf.config import Config
from appxf.gui import AppxfOption

config = Config()
# config.language['USER'] = 'Benutzer'
# config.language['Cancel'] = 'Abbrechen'
# config.language['OK'] = 'Schließen'

config.add_section("EMPTY")
# Simple string:
config.add_section(
    "USER",
    {
        "Email": AppxfOption(type="email"),
        "Rolle": AppxfOption(type="str"),
        "Ist Admin": AppxfOption(type="bool"),
        "Irgendein Integer": AppxfOption(type="int"),
    },
)
config.section("USER").set("Email", "empty@email.com")
config.section("USER").set("Rolle", "Depotbetreuer")
config.section("USER").set("Ist Admin", True)
config.section("USER").set("Irgendein Integer", 15)

gui = EditConfigWindow(config, "USER")
gui.mainloop()

# config.open_edit_gui('USER', title='Einstellungen für {0}')
# print('..repeat..')
# config.open_edit_gui('USER')

print("DONE")
