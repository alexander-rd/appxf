### Configuration transfer via REGISTRY (SDT #14, Kiss #26)
**Status:** mechanism seems to work to transfer configuration data via registration
response to the registering user. Open is the GUI perspective of this behavior.

To enable GUI testing, I can either:
 (A) Setup ONE GUI test with two applications (user and admin)
     running in parallel and with supporting a multi-step procedure.
 (B) Automatically prepare both instances to a certain point and, within each
     manual test case, only instantiate ONE GUI, performing the ONE particular
     step. Support that likely needs to be added is: assertions during setup
     and assertions at teardown of the test. Especially tests at teardown shall
     avoid manual checks of expected results.

Clearly, (B) should be realized. Not unlikely, the sketched additions can be
avoided. I would build a GUI application on top of the existing application
harness. ?? Is this GUI application generic or specific to registration tests?
Well, there is nothing wrong if the first version is specific to the
registration test.

### Setting names empty
I have SettingDicts (like login) for which the name options are empty. This leads to empty labels when puttint the SettingSingleFrame thingys.