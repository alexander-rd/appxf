from kiss_cf import property
from kiss_cf import logging

# TODO: review this code and get rid of it by OptionProperty. Consider
# renaming. Consider the connected test caes and usage of those classes and
# connected classes.

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
    prop = property.KissProperty(None)
    assert str(prop) == 'mutable KissProperty: None (invalid)'
    assert prop.value is None

    prop = property.KissString()
    assert str(prop) == 'mutable KissString:  (valid)'
    assert prop.value == ''

    prop = property.KissEmail()
    assert str(prop) == 'mutable KissEmail:  (invalid)'
    assert prop.value == ''

    prop = property.KissBool()
    assert str(prop) == 'mutable KissBool: False (valid)'
    assert prop.value is False


def verify_input_list(type, valid_list, valid_result_map):
    for value in all_values:
        prop = type()
        initial_value = prop.value
        initial_valid = prop.valid

        prop.value = value

        if value in valid_list:
            expected_value = valid_result_map.get(value, value)
            assert prop.valid is True, (
                f'Expected valid for {value} ({value.__class__})'
                f', got: {prop}')
            assert prop.value == expected_value, (
                f'Values don\'t match for {value} ({value.__class__})'
                f', got: {prop}')
        else:
            assert prop.valid == initial_valid, (
                f'Expected {initial_valid} validity for '
                f'{value} ({value.__class__})'
                f', got: {prop}')
            assert prop.value == initial_value, (
                f'Expected initial value {initial_value} for {value} '
                f'({value.__class__}), got: {prop}')


def test_string_validate():
    verify_input_list(
        property.KissString,
        string_values + email_values
        + bool_string_values + integer_string_values,
        dict())


def test_email_validate():
    verify_input_list(
        property.KissEmail, email_values, dict())


def test_bool_validate():
    verify_input_list(
        property.KissBool,
        bool_string_values + bool_values,
        {'True': True, 'False': False,
         '1': True, '0': False,
         'yes': True, 'No': False})


# TODO: cannot overwrite with wrong value - also for KissProperty (to cover the
# one validate line)

# TODO: backup and restore must also restore validity properly

if __name__ == '__main__':
    print('Hello!')
    test_bool_validate()
