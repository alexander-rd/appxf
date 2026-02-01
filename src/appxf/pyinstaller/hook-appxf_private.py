'''PyInstaller hook registration
'''
from PyInstaller.utils.hooks import collect_data_files

# Add translation mo files to resources:
datas = collect_data_files(
    package='appxf',
    includes=['locale/*/LC_MESSAGES/*.mo'])
