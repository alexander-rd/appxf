from datetime import date

project = 'APPXF'
html_title = 'APPXF'
author = 'the contributors of APPXF (github.com/alexander-nbg/appxf)'
copyright = f'{date.today().year} the contributors of APPXF (github.com/alexander-nbg/appxf)'

extensions = [
    'myst_parser',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

source_suffix = {
    '.md': 'markdown',
}

master_doc = 'index'

html_theme = 'pydata_sphinx_theme'

html_theme_options = {
    'github_url': 'https://github.com/alexander-nbg/appxf',
}
