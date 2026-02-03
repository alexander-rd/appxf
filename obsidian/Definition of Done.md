<!--Copyright 2026 the contributors of APPXF (github.com/alexander-rd/appxf)-->
<!--SPDX-License-Identifier: 0BSD-->
# Code
* flake succeeds
* unit test coverage (see [[APPXF Test Strategy]])
* ToDo remarks for any known open topics (including planning tickets and referenced in ToDos `"ToDo #42"`)
* Ticket concluding remarks
	* Planning follow-up tickets
* Localization: MO/PO files are updated (all translations available)
* Functions are documented
	* How much depends on exposure
	* Minimum for public functions: Purpose (summary) and type annotation (including returns)
# Features on Application Level
If a feature is visible for final applications, it needs:
* documentation (updates) in the feature section
* automated BDD testing for behavior (application harness)
* manual test for user experience (application harness GUI)
* reference usage
	* documentation
	* testing the exact code in the testing
* All bullet points below since it is always also a feature for application developers
# Features for Application Developers
If a feature is visible for developers, it needs:
* optional: mentioning in the [[Implementation Features]]
* documentation in modules
	* further details TBD
# Monitoring Wishlist
* Health dashboard would report
	* ~~Flake8 status~~ (something that's always kept green does not need monitoring)
	* ToDo numbers
	* Coverage Numbers
* Tracing (documentation to code; to ensure documentation is present)
* Diff branch against head and filter any new TODO. Intend is to enable a review before conclusions.
	* Fallback: scan branch in github