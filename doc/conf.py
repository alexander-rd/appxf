# Copyright 2026 the contributors of APPXF (github.com/alexander-nbg/appxf)
# SPDX-License-Identifier: 0BSD
from datetime import date
from pathlib import Path

project = "APPXF"
html_title = "APPXF"
author = "the contributors of APPXF (github.com/alexander-nbg/appxf)"
copyright = (
    f"{date.today().year} the contributors of APPXF (github.com/alexander-nbg/appxf)"
)

extensions = [
    "myst_parser",
    "sphinxcontrib.plantuml",
    "sphinx.ext.duration",
]

myst_enable_extensions = [
    "colon_fence",
    #'linkify',
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

source_suffix = {
    ".md": "markdown",
}

master_doc = "index"

html_theme = "pydata_sphinx_theme"

html_theme_options = {
    "github_url": "https://github.com/alexander-nbg/appxf",
    "announcement": (
        "<b>Documentation is not usable</b>: "
        "APPXF is currently transitioning from private repo. "
        'See <a href="https://github.com/alexander-nbg/appxf/issues/48" '
        'target="_blank">issue #48</a>.'
    ),
}

project_root = Path(__file__).resolve().parent.parent
plantuml_jar = project_root / "doc" / "plantuml.jar"
plantuml = f"java -jar {plantuml_jar}"
plantuml_args = ["-I", project_root / "doc"]
plantuml_output_format = "svg"
plantuml_syntax_error_image = True
