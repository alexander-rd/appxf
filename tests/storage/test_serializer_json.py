# Copyright 2025-2026 the contributors of APPXF (github.com/alexander-rd/appxf)
# SPDX-License-Identifier: Apache-2.0
''' Test all serializer classes '''
import pytest

from appxf.storage import JsonSerializer, Serializer

from tests.storage.test_serializer_base import BaseSerializerTest

class TestJsonSerializer(BaseSerializerTest):
    def _get_serializer(self) -> Serializer:
        return JsonSerializer()
