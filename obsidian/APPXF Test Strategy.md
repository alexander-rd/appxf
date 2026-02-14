<!--Copyright 2026 the contributors of APPXF (github.com/alexander-rd/appxf)-->
<!--SPDX-License-Identifier: 0BSD-->
The test strategy considers the following two test levels:
* __Unit Tests__ are driven by code coverage of the individual modules and *should cover 100%* (lines and branches) while *80% branch coverage is acceptable for initial versions*. While focusing on individual modules, tests may or may not cut free interfaces to other modules. Modules include GUI modules which must be covered by manual tests.
* __Feature Tests__ are driven by the APPXF supported ***use cases*** and ***performance targets*** while *appropriate coverage is determined by review*. If use cases are already well covered by the unit tests, they do not need to be repeated but a corresponding file shall still be present with corresponding arugments. Feature tests shall use the APPXF implementation as-is wherever possible.

Remark: While use cases like login/registration involve many modules like GUI elements, storage and settings which shall also ensure proper interaction between the APPXF modules, the term *integration test* will not be used. Rationale: there is no integration, APPXF is *one* package of cross-functional modules.

The following details shall be considered:
* __Backwards Compatibility__ shall be ensured by either unit tests or feature tests (not yet available).
* Test execution shall be __automated__. For manual test cases, this implies: results are checked-in, compared against changes and their execution is validated in an automated test case. Test coverage from (valid) manual test executions will be merged with the automated ones.

# Test Methods
All methods, mentioned below may be combined!
## Pytest
The default approach is straight-forward pytest test cases. Pytest is preferred (not mandated) for automated unit tests since BDD test would add the complexity of two-files, a more abstract implementation and the abstraction of the Gherkin language.
## Behavior Driven Tests (bdd)
They are included in a pytest run and just use the capabilities of python-bdd with Gherkin syntax. They are preferred for use case based feature testing and the added complexity in comparison to plain pytest is reasonable since the feature files shall represent functional requirements.
## Manual Tests (GUI)
__This is work in progress.__ Most of the required helpers are not yet existing! The idea comprises steps in the automation via TOX:
* updating the manual test case database (validity of test cases based on code changes and scanning for existing manual test cases)
* a test case that is FAILING if any planned test case has no valid test execution
* merging the coverage of valid manual test case executions with the automated unit tests or feature tests
and scripting (or an application) assisting with:
* triggering the steps mentioned above in TOX
* listing invalid test cases
* triggering test case execution including adding to database

During manual test case execution:
* the tester has one window with the test descriptions (things to check) and
commenting results with OK/FAILED
* the tester gets the window or frame in a second window to play around
* the test execution may include additional checks after test execution

#TODO: General TODO of implementation and mentioning a specific example of such a GUI test. Further details likely require a separate markdown page. See ticket #25

#TODO: For application level testing, the test preparation steps *must be separated*  for the coverage. Example: even though the user data (login) preparation is executed for a test case concerning registry, the login steps are not tested in such a test case. Hence, the test case for registration should not be invalidated by changing the login implementation. This is a trade-off.
## Application Testing
### Application Harness
**Definition.** In APPXF context, an application harness aggregates objects for a basic application. It ***does*** provide methods for operations on the aggregated objects while it ***does not*** provide any user interface or enforces behavior more than initialization.

The __AppHarness__ for testing is stored in `tests/_fixtures/app_harness.py`. The fixtures in `tests/fixtures/application.py` may combine several ApplicationMock instances. They are prepared and used as follows:
1. The file structure is prepared once for the appxf library version at location:
   `.testing/app_\<context\>_\<appxf version\>`.
2. The prepared folder is copied for the specific test case. The dictionary of the fixture contains entries like `app_user` which return an ApplicationMock object. This ApplicationMock includes all objects and required paths in context of the ApplicationMock.
### Application Harness User Interface
**Definition.** In APPXF context, an application harness user interface just puts a default user interface on top of an application harness.

## Backwards Compatibility
__This is work in progress.__ Most of the required helpers are not yet existing!

Testing of backwards compatibility shall be based on the __ApplicationMock__ fixtures with the following procedure:
* At a release, the appxf-version specific prepared file structures <code>.testing/app_*</code> are checked-in while the release version of the main branch is increased.
* The behavior driven sceanrio outlines are extended by incorporating the old version.

#TODO: Mention a specific example of such a test application fixture.
#TODO: It may be necessary to also use this approach for non BDD tests.
# Additional Guidelines
## Folder Structure
Unit tests are all in <code>tests</code> and in subfolders according to the modules in <code>src</code>. Different test files exist (see test methods):
* normal unit tests should use the naming of the <code>src</code> file with
the prefix <code>test_</code>.
* manual test cases for GUI elements also use the naming of the `src` file with the prefix `manual_` but need to add further details into the file name since each file represents one test case.
* behavior driven tests (bdd) need to use the prefix `test_bdd` and come along with a second `*.feature` file.

Feature tests are all stored in <code>feature_tests</code> while following the same folder and file name conventions. Examples:
* <code>tests/test_buffer.py</code>
* <code>tests/storage/test_ram.py</code>
* <code>tests/gui/manual_setting_dict_column_frame.py</code>
* <code>tests_features/sync/test_bdd_sync.py</code> and
* <code>tests_features/sync/test_bdd_sync.feature</code>

__Rationale:__ Feature tests and unit tests are separated because coverage is evaluated separately. Since tox is not able to use an input like <code>tests/feature_*</code> for pytest, the tests are separated on the topmost level. The prefix <code>test_bdd</code> is mandated to remain consistent if behavior tests are combined with normal unit tests for the same module.

#TODO: file guideline should include the fixtures folder.