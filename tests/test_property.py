from kiss_cf import property
from kiss_cf import logging

logging.console_handler.setFormatter(logging.file_formatter)

string_values = [
    '', 'Üäö,.-#+^;:_*`?!', "'", '@~\\|<>',
    'abcdefghijklmnopqrstuvwxyz',
    'leer linebreak\n  tab\t bla']
email_values = [
    'mail@something.de',
    'some.subdomain@domain-with-minus.org']

bool_values = [True, False]
bool_string_values = [
    'True', 'False', 'yes', 'No', '0', '1'
    ]

integer_values = [0, 1, 5, 100, 2 ^ 32, -1, -42, -2 ^ 33]
integer_string_values = [
    '0', '1', '-1', '100',
    '12345678901234567890',
    '-12345678901234567890']

no_values = [property.KissProperty, None, Exception]

all_values = (
    string_values + email_values +
    bool_values + bool_string_values +
    integer_values + integer_string_values +
    no_values)


def test_property_after_init():
    prop = property.KissProperty()
    assert str(prop) == 'mutable KissProperty: None (invalid)'
    assert prop.value is None

    prop = property.KissString()
    assert str(prop) == 'mutable KissString: None (invalid)'
    assert prop.value == ''

    prop = property.KissEmail()
    assert str(prop) == 'mutable KissEmail: None (invalid)'
    assert prop.value == ''

    prop = property.KissBool()
    assert str(prop) == 'mutable KissBool: None (invalid)'
    assert prop.value is False


def verify_input_list(type, valid_list, default_value):
    for value in all_values:
        prop = type()
        prop.value = value

        if value in valid_list:
            assert prop.valid is True, (
                f'Expected valid for {value} ({value.__class__})'
                f', got: {prop}')
            assert prop.value == value, (
                f'Values don\'t match for {value} ({value.__class__})'
                f', got: {prop}')
        else:
            assert prop.valid is False, (
                f'Expected invalid for {value} ({value.__class__})'
                f', got: {prop}')
            assert prop.value == default_value, (
                f'Expected default value for {value} '
                f'({value.__class__}), got: {prop}')


def test_string_validate():
    verify_input_list(
        property.KissString,
        string_values + email_values
        + bool_string_values + integer_string_values,
        '')


def test_email_validate():
    verify_input_list(
        property.KissEmail, email_values, '')


def test_bool_validate():
    verify_input_list(
        property.KissBool, bool_string_values + bool_values, False)


# TODO: cannot overwrite with wrong value - also for KissProperty (to cover the
# one validate line)

if __name__ == '__main__':
    print('Hello!')
    test_bool_validate()
