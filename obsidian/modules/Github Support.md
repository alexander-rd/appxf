# Testing
```plantuml
@startuml
!theme cerulean

|Application|
start
:<b>workflows/test.yml</b>;
|APPXF|
:<b>actions/setup/action.yml</b>(python version)
Plus appxf_private token as long as not appxf;

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
	* Calls: **appxf_private/github/test**@main (os, python version)
		* checkout repo
		* checkout appxf_private (if not running on appxf_private)
		* Calls: **./.github/actions/setup** (only if on appxf_private)
		* Calls: **appxf_private/.github/actions/setup** (if not on appxf_private)
		* install appxf_private
		* tox preparation
		* run tox (if not appxf_private) << wrong

# TODO:
* User RUNNER_OS instead of passing the os as argument.