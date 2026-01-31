'''PyInstaller hook registration
'''
from PyInstaller.utils.hooks import collect_data_files

# Add translation mo files to resources:
datas = collect_data_files(
    package='kiss_cf',
    includes=['locale/*/LC_MESSAGES/*.mo'])
