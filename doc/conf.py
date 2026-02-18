project = 'APPXF'
author = 'APPXF contributors'

extensions = [
    'myst_parser',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

source_suffix = {
    '.md': 'markdown',
}

master_doc = 'index'

html_sidebars = {
    '**': [
        'navigation.html',
        'searchbox.html',
    ]
}
