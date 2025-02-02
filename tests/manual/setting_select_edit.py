from helper import ManualTestHelper
from kiss_cf.gui.setting_dict import SettingDictSingleFrame
from kiss_cf.setting import Setting, SettingDict

# Scope: SettingSelect edit options functionality

tester = ManualTestHelper('''
TBD
''')  # noqa: E501

settingOne = Setting.new('select::string',
    options={'Long Broken Text': '''Lorem ipsum dolor sit amet,

consetetur sadipscing elitr, sed diam nonumy eirmod tempor
invidunt ut labore et dolore magna aliquyam erat, sed diam
voluptua. At vero eos et accusam et justo duo dolores et ea rebum.
Stet clita kasd gubergren, no sea takimata sanctus est Lorem ipsum
dolor sit amet. Lorem ipsum dolor sit amet, consetetur sadipscing
elitr, sed diam nonumy eirmod tempor invidunt ut labore et dolore
magna aliquyam erat, sed diam voluptua. At vero eos et accusam et
justo duo dolores et ea rebum. Stet clita kasd gubergren, no sea
takimata sanctus est Lorem ipsum dolor sit amet. Lorem ipsum dolor
sit amet, consetetur sadipscing elitr, sed diam nonumy eirmod
tempor invidunt ut labore et dolore magna aliquyam erat, sed diam
voluptua. At vero eos et accusam et justo duo dolores et ea rebum.
Stet clita kasd gubergren, no sea takimata sanctus est Lorem ipsum
dolor sit amet.

Duis autem vel eum iriure dolor in hendrerit in vulputate velit esse molestie
consequat, vel illum dolore eu feugiat nulla facilisis at vero eros et accumsan
et iusto odio dignissim qui blandit praesent luptatum zzril delenit augue duis
dolore te feugait nulla facilisi. Lorem ipsum dolor sit amet, consectetuer
adipiscing elit, sed diam nonummy nibh euismod tincidunt ut laoreet dolore
magna aliquam erat volutpat.''',
             'Long Single Line': 'Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed diam nonumy eirmod tempor invidunt ut labore et dolore magna aliquyam erat, sed diam voluptua. At vero eos et accusam et justo duo dolores et ea rebum. Stet clita kasd gubergren, no sea takimata sanctus est Lorem ipsum dolor sit amet. Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed diam nonumy eirmod tempor invidunt ut labore et dolore magna aliquyam erat, sed diam voluptua.',
             'Short': 'String',
             }, name='SelectString')
settingOne.options['mutable'] = True
settingOne.base_setting.gui_options['height'] = 20
settingOne.base_setting.gui_options['width'] = 60

settingTwo = Setting.new('select::int',
    options={'1 Eins': 1, '2 Zwei': 2, '3 Drei': 3},
    name='Integers')
settingTwo.options['mutable'] = True

setting = SettingDict(data={'SelectString': settingOne, 'Integer': settingTwo})

tester._run_frame(SettingDictSingleFrame,
                 setting)
