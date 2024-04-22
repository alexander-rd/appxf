
import pytest
from kiss_cf.storage import StorageMaster, StorageMasterMock, KissStorableError
from kiss_cf.property import KissPropertyDict
from kiss_cf.config import Config, KissConfigError

def test_config_initialization_state():
    config = Config()
    assert len(config.sections) == 0

def test_config_fill_section():
    config = Config()
    # just a view varianty of propert init. Full testing in scope of
    # KissPropertyDict.
    config.add_section('TEST').add(email=('email',),
                                   string=(str, 'hello'),
                                   integer=42)
    # Check sections and values
    assert config.sections == ['TEST']
    section = config.section('TEST')
    assert isinstance(section, KissPropertyDict)
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
    storage_master_mock = StorageMasterMock()
    config = Config(default_storage=storage_master_mock)
    config.add_section('TESTA').add(test='A')
    config.add_section('TESTB').add(test='B')
    config.add_section('TESTC').add(test='C')
    config.store()
    # new config and load
    config_restore = Config(default_storage=storage_master_mock)
    config_restore.add_section('TESTA').add(test=(str,))
    config_restore.add_section('TESTB') # no added options will NOT load it
    config_restore.add_section('TESTC').add(test=(str,))
    config_restore.load()
    assert config_restore.section('TESTA')['test'] == 'A'
    assert list(config_restore.section('TESTB').keys()) == []
    assert config_restore.section('TESTC')['test'] == 'C'

def test_config_store_load_custom_storage():
    storage_master_mock_A = StorageMasterMock()
    storage_master_mock_B = StorageMasterMock()
    config = Config(default_storage=storage_master_mock_A)
    config.add_section('TESTA').add(test='A')
    config.add_section('TESTB', storage_master=storage_master_mock_B).add(test='B')
    config.store()
    # new config and load - but this time, B does use default storage master A
    config_restore = Config(default_storage=storage_master_mock_A)
    config_restore.add_section('TESTA').add(test=(str,))
    config_restore.add_section('TESTB').add(test=(str,))
    config_restore.section('TESTA').load()
    assert config_restore.section('TESTA')['test'] == 'A'
    with pytest.raises(KissStorableError) as exc_info:
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
