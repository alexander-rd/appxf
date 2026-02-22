#!/bin/bash
# Copyright 2026 the contributors of APPXF (github.com/alexander-nbg/appxf)
# SPDX-License-Identifier: 0BSD

set -e

PLANTUML_URL='https://github.com/plantuml/plantuml/releases/download/v1.2026.1/plantuml.jar'
PLANTUML_JAR='doc/plantuml.jar'

if [[ -f "$PLANTUML_JAR" ]]; then
    echo "PlantUML jar already present at $PLANTUML_JAR"
else
    echo "Downloading PlantUML v1.2026.1 to $PLANTUML_JAR..."
    mkdir -p "$(dirname "$PLANTUML_JAR")"
    wget -q -O "$PLANTUML_JAR" "$PLANTUML_URL"
    echo "PlantUML jar downloaded successfully."
fi
