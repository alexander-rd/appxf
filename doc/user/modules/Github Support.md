<!--Copyright 2026 the contributors of APPXF (github.com/alexander-nbg/appxf)-->
<!--SPDX-License-Identifier: 0BSD-->
# Testing
```plantuml
@startuml
!theme cerulean

|Application|
start
:<b>workflows/test.yml</b>;
|APPXF|
:<b>actions/setup/action.yml</b>(python version)
Plus appxf token as long as not appxf;

|Application|
:<b>actions/setup/action.yml</b>
(optional) for application
specific installations;

|APPXF|
:<b>.github/actions/run-tox</b>
Install, cache venv and run tox.;
|Application|
end
@enduml
```
## Current Setup
* Entry point: **.github/workflows/test.yml**
	* Calls: **appxf/github/test**@main (os, python version)
		* checkout repo
		* checkout appxf (if not running on appxf)
		* Calls: **./.github/actions/setup** (only if on appxf)
		* Calls: **appxf/.github/actions/setup** (if not on appxf)
		* install appxf
		* tox preparation
		* run tox (if not appxf) << wrong

# TODO:
* User RUNNER_OS instead of passing the os as argument.