# KISS_CF Test Strategy

Goals
-----
KISS Cross Functionals need to consider the types of source code within the library:
 * __Any implementation__ should have 100% function coverage. However, python coverage does only support line and branch coverage. Putting this goal in numbers results in: __*80% line coverage*__.
 * __basic functionality__ should be fully tested with __*100% branch coverage*__.
 * __convenience functionality__ should cover all use cases and most but not all error cases.
 * __GUI implementation__ may be tested only manually (no automated testing is yet available)

 In addition to the basic test coverage, the testing must consider future interface changes, meaning: __the testing include backwards compatibility__.

Basic Functionality
-------------------
Basic functionality is tested via unit testing in <code>tests/test_\<module\>.py</code> or <code>tests/\<module\>/test_\<sub-module\>.py</code>. Unit testing may be anything done by pytest and does not require cutting all interfaces free. It may use the ApplicationMock (see below) as well as behavior driven testing.

Convinience Functionality
-------------------------

Convinience functions shall be tested by behavior driven tests in context of the __ApplicationMock__ (see below). The implementation shall consider:
    * Reuse of actions and checks across features
    * Allowing to build up complex actions from simpler actions
Additionally, especially during build-up of new features, the testing can happen in an isolated fashion where only basic use cases are covered.

GUI
---
GUI implementations shall come along with test applications, showing the GUI to allow "playing around. The concept is not conclusive, yet but may consider:
  * A separate GUI to play around
  * A GUI that is using a __test application fixture__ in the background.

\# TODO: Mention a specific example of such a GUI test.

ApplicationMock
---------------
The __ApplicationMock__ in <code>tests/fixtures/application_mock.py</code> mimics an application sufficiently complex for advanced test cases. The fixtures in <code>tests/fixtures/application.py</code> may combine several ApplicationMock instances. They are prepared and used as follows:
  1. The file structure is prepared once for the kiss_cf library version at location: <code>.testing/app_\<context\>_\<kiss_cf version\></code>.
  1. The prepared folder is copied for the specific test case. The dictionary of the fixture contains entries like <code>app_user</code> which return an ApplicationMock object. This ApplicationMock includes all objects and required paths in context of the ApplicationMock.

Backwards Compatibility
-----------------------

Testing of backwards compatibility shall be based on the __ApplicationMock__ fixtures with the following procedure:
  * At a release, the kiss_cf-version specific prepared file structures <code>.testing/app_*</code> are checked-in while the release version of the main branch is increased.
  * The behavior driven sceanrio outlines are extended by incorporating the old version.

\# TODO: Mention a specific example of such a test application fixture.

\# TODO: It may be necessary to also use this approach for non BDD tests.

