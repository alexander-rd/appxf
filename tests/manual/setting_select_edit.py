from helper import ManualTestHelper
from kiss_cf.gui.setting_dict import SettingDictSingleFrame
from kiss_cf.setting import AppxfSettingSelect, AppxfSetting, SettingDict
from kiss_cf.gui import SettingSelectFrame

# Scope: SettingSelect edit options functionality

tester = ManualTestHelper('''
TBD
''')  # noqa: E501

settingOne = AppxfSetting.new('select::string',
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
settingOne.base_setting_kwargs['height'] = 20
settingOne.base_setting_kwargs['width'] = 60

settingTwo = AppxfSetting.new('select::int',
    options={'1 Eins': 1, '2 Zwei': 2, '3 Drei': 3},
    name='Integers')
settingTwo.options['mutable'] = True

setting = SettingDict(data={'SelectString': settingOne, 'Integer': settingTwo})

# TODO: remove "setting name" from middle entry field

# TODO: larger problem on GUI settings for the base_setting and for the
# extended_setting. They have to be differentiated - like: width of dropdown
# entry is not the same as width for the value entry.

# TODO: to incorporate the Close/Done button, the GUI should be redesigned:
#  1) Delete/Save buttons in the same first row.
#  2) Upon Save, the new name must be defined by another window (Cancel & OK)
#  3) (1) and (2) is a FRAME where Save/Delete buttons are present if the
#     setting is mutable.
#  4) The Close button is added to a window that uses this Frame (OK only since
#     it does not store)

# TODO: After delete and now since elements are sorted (in GUI), the default
#    setting goes to an "arbitrary element" since the first in the internal
#    dict is arbitrary when sorted. Expected would be to select the one after
#    or the last in sorted list if nothing else is left. >> A bit more complex
#    but nothing wild. >> Option delete functionality should be within the
#    setting. >> Same for getting the sorted list?? >> most general would be to
#    provide a sorting function (for strings).

tester._run_frame(SettingDictSingleFrame,
                 setting)
