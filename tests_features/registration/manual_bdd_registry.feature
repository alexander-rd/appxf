# Copyright 2025-2026 the contributors of APPXF (github.com/alexander-rd/appxf)
# SPDX-License-Identifier: Apache-2.0
Scenario: user registration
Given an admin initialized application AppAdmin
And an unlocked but unregistered application AppUser

When application AppUser is opened
And the password is entered
Then the registration window is displayed
And the registration request can be copied
# above is manual

# all steps manual
When application AppAdmin is opened
And MAN the registration request is entered
Then MAN the user information is displayed
And MAN the validity of the request is displayed
And MAN the requested roles are displayed
And MAN the registration response can be copied

When MAN the registration request is accepted
Then the user of AppUser is visible in AppAdmin
And the user of AppUser is visible in the sync location

When application AppUser is continued
And MAN the user enters the registration response
Then MAN the user should have the full application running
And registration config settings are available in AppUser
And the user database is updated

# What's my problem to continue?
#  1) I don't know how the test should look like (method)?
#  2) I have doubts on an efficient implementation?
#
# What are basic prerequisites?
#  1) Any test (BDD) with an opened application (login screen)
#  BUT: This would be obsolete if I'm not testing full applications
#  BUT-BUT: I want to have validated sample code
#  BUT-BUT-BUT: This is not current priority
# >> So, my problem is PRIORITIZATION of my activities.
# >> In this case, the application test is not the right time!