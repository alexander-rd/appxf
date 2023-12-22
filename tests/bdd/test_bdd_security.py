from pytest_bdd import scenarios, given, when, then, parsers

# scenarios('../features/registration.feature')

@given('a fresh tool installation')

@when('opening the tool')
def tool_open():
    pass

@when('no user data exists')
def data_no_user_data():
    pass

@then('user data shall be generated')
def data_user_data():
    pass
