#!/usr/bin/env bash

if [[ "${1-}" == '--clean' ]]; then
    rm -rf doc/_build
    sphinx-build -M html doc doc/_build
fi

sphinx-build -M html doc doc/_build