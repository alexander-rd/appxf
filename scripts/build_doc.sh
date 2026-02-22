#!/bin/bash
# Copyright 2026 the contributors of APPXF (github.com/alexander-nbg/appxf)
# SPDX-License-Identifier: 0BSD

set -e

# Ensure PlantUML jar is available
bash "$(dirname "$0")/_ensure_plantuml_jar.sh"

if [[ "${1-}" == '--clean' ]]; then
    rm -rf doc/_build
    sphinx-build -M html doc doc/_build --exception-on-warning -v
fi

sphinx-build -M html doc doc/_build --exception-on-warning -v
