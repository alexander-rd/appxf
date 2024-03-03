# KISS_CF Test Strategy

Goals
----
KISS Cross Functionals need to consider the types of source code within the library:
 * __Any implementation__ should have 100% function coverage. However, python coverage does only support line and branch coverage. Putting this goal in numbers results in: __*80% line coverage*__.
 * __basic functionality__ should be fully tested with __*100% branch coverage*__.
 * __convenience functionality__ should cover all use cases and most but not all error cases.
 * __GUI implementation__ may be tested only manually (no automated testing is yet available)

 In addition to the basic test coverage, the testing must consider future interface changes, meaning: __the testing include backwards compatibility__.

Basic functionality
-------------------
Basic functionality is tested via unit testing in <code>tests/test_\<module\>.py</code> or <code>tests/\<module\>/test_\<sub-module\>.py</code>.

Convinience Functionality
-------------------------

Convinience functions shall be tested by behavior driven tests in context of a __test application fixture__ which is prepared and used as follows:
  1. The test application is prepared once for the kiss_cf library version at location: <code>.testing/app_\<context\>_\<kiss_cf version\></code>.
  1. The prepared folder is copied for the specific test case and prepared environment consists of:
      * Root storage location of the files
      * Application configuration (which files are used)
      * Access to all objects of the application
  1. The implementation of the test cases shall consider:
      * Reuse of actions and checks across features
      * Allowing to build up complex actions from simpler actions
Additionally, especially during build-up of new features, the testing can happen in an isolated fashion where only basic use cases are covered.

GUI
---
GUI implementations shall come along with test applications, showing the GUI to allow "playing around. The concept is not conclusive, yet but may consider:
  * A separate GUI to play around
  * A GUI that is using a __test application fixture__ in the background.

\# TODO: Mention a specific example of such a GUI test.

Backwards Compatibility
-----------------------

Testing of backwards compatibility shall be based on the __test application fixtures__ with the following procedure:
  * At a release, the kiss_cf-version specific prepared application fixtures are checked-in while the release version of the main branch is increased.
      * Test cases would now test, assuming only the new kiss_cf version.
  * The behavior driven sceanrio outlines are extended by incorporating the old version.

\# TODO: Mention a specific example of such a test application fixture.

