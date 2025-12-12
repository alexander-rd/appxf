### Configuration transfer via REGISTRY (SDT #14, Kiss #26)
**Status:** mechanism seems to work to transfer configuration data via registration
response to the registering user. Open is the GUI perspective BUT before this, it must be clarified how the request/response is exchanged. Currently, this is a bytes object handled within python. Needed is a file based exchange.

It is already clear that I need to handle request/response via *one* file. This poses some challenges:
* currently, the interface is just "bytes" (which could be streamed into a file)

Drafting Solution:
* Response/Request already generate the bytes via serializer. Those objects can handle well any future encryption and signing.
* The bytes can just be dumped into a file and loaded from there. ***Any additional handling is done by Response/Request objects***.
GUI Procedure:
1. get folder or file name via GUI
2. get bytes for request from registry (load bytes for response)
3. write bytes to file (send bytes of response to registry)

**Observation.** While adding the GUI behavior it becomes apparent that the functional analysis in problem domain is missing. It appears in questions like: "what if the user needs to raise a new registration requests to repair something in the configuration (utilizing the registration config transfer)" or "what if the user was already registered - should there be an option to generate a response for an existing user". >> I should start adding some diagram on this level (and resolve the drawio ones).