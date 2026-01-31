
import pytest
from appxf_private.storage import AppxfStorableError, RamStorage, Storage
from appxf_private.setting import SettingDict
from appxf_private.config import Config, KissConfigError

@pytest.fixture(autouse=True)
def setup():
    Storage.reset()

def test_config_initialization_state():
    config = Config()
    assert len(config.sections) == 0

def test_config_fill_section():
    config = Config()
    # just a view varianty of propert init. Full testing in scope of
    # KissPropertyDict.
    config.add_section(
        'TEST', settings = {
            'email': ('email',),
            'string': (str, 'hello'),
            'integer': 42
            })
    # Check sections and values
    assert config.sections == ['TEST']
    section = config.section('TEST')
    assert isinstance(section, SettingDict)
    assert config.section('TEST')['email'] == ''
    assert config.section('TEST')['string'] == 'hello'
    assert config.section('TEST')['integer'] == 42
    # write valid email (not really a config test, but a valid example how code
    # would look like):
    config.section('TEST')['email'] = 'someone@nowhere.com'
    assert config.section('TEST')['email'] == 'someone@nowhere.com'

def test_config_empty_section():
    config = Config()
    config.add_section('TEST')
    assert config.sections == ['TEST']

def test_config_store_load():
    config = Config(default_storage_factory=RamStorage.get_factory())
    config.add_section('TESTA', settings = {'test': 'A'})
    config.add_section('TESTB', settings = {'test': 'B'})
    config.add_section('TESTC', settings = {'test': 'C'})
    config.store()
    # new config and load
    config_restore = Config(default_storage_factory=RamStorage.get_factory())
    config_restore.add_section('TESTA', settings = {'test': (str,)})
    config_restore.add_section('TESTB') # no added options will NOT load it
    config_restore.add_section('TESTC', settings = {'test': (str,)})
    config_restore.load()
    assert config_restore.section('TESTA')['test'] == 'A'
    assert list(config_restore.section('TESTB').keys()) == []
    assert config_restore.section('TESTC')['test'] == 'C'

def test_config_store_load_custom_storage():
    RamStorage.reset()
    factory_a = RamStorage.get_factory(ram_area='mock_A')
    factory_b = RamStorage.get_factory(ram_area='mock_B')
    config = Config(default_storage_factory=factory_a)
    config.add_section('TESTA')
    config.section('TESTA')['test'] = 'A'
    config.add_section('TESTB', storage_factory=factory_b)
    config.section('TESTB')['test'] = 'B'
    config.store()
    # new config and load - but this time, B does use default storage master A
    config_restore = Config(default_storage_factory=factory_a)
    config_restore.add_section('TESTA')['test'] = (str,)
    config_restore.add_section('TESTB')['test'] = (str,)
    config_restore.section('TESTA').load()
    assert config_restore.section('TESTA')['test'] == 'A'
    with pytest.raises(AppxfStorableError) as exc_info:
        config_restore.section('TESTB').load()
    assert 'Storage does not exist' in str(exc_info.value)

def test_config_adding_existing_section():
    config = Config()
    config.add_section('TEST')
    with pytest.raises(KissConfigError) as exc_info:
        config.add_section('TEST')
    assert 'Cannot add section TEST' in str(exc_info.value)

def test_config_access_non_existing_section():
    config = Config()
    with pytest.raises(KissConfigError) as exc_info:
        config.section('TEST')
    assert 'Cannot access section TEST' in str(exc_info.value)
