# Copyright 2025-2026 the contributors of APPXF (github.com/alexander-rd/appxf)
# SPDX-License-Identifier: Apache-2.0

# Prerequisite: I need two application instances:
#  1) An initialized admin account
#  2) An user account with local data (login complete, registration pending)

# Step 1 [User Application]: user should get a registration request pop-up.
# Tester must COPY the registration request somewhere

# Step 2.1 [Admin Application]: admin opens the registration response form.
# Tester must PASTE the registration request.

# Step 2.2 [Admin Application]: admin verifies the request data and generates
# the registration response. Tester must COPY the registration response
# somewhere.
#
# Expectation: admin application now knows the new user

# Step 3 [User Application]: user PASTES the registration response
#
# Expectation: user application is now fully initialized and config information
# is available.

# A further use case must use a second user account to verify that a second
# user will get the new user information available.

# ?? Do I really have a full application with tasks started from the
# application window OR do I only test GUI elements?
#  >> APPXF should provide a simple "all included" solution but this would
#  >> require an application frame that adds menu items if the Registration
#  >> object is provided >> added complexity.
#  >>
#  >> The alternative would just test the GUI elements and an application must
#  >> add corresponding buttons themselves.. ..while the user initialization is
#  >> generic.. ..the admin steps must be added SOMEWHERE to the menu.
#  >>
#  >> I think, overall - there should be default menu items as soon as there is
#  >> the login feature (change password and user data). But APPXF should only
#  >> proide a template and guideline - it's scope is NOT to make an
#  >> application frame
#
# Result: Only concatenated GUI elements or callable parts - NO full
# application.
#
# Narf-However: There should be a sample implementation for an application and
# Admin-Initialization as well as User-Initialization should be checked based
# on such code.