**Situation and Problem.** An application maintains data that shall be persisted during sessions. But there are more details to consider. Shall the data be stored human readable or in binary format? Shall it be encrypted? Shall it be shared with other application instances?

**Feature.** The storage concept is an abstraction allowing you to focus on the function your are implementing and pick the storage behavior from the APPXF library. The behavior is split into **storage locations**:
* on local disk (LocalStorage) or
* via FTP,
**storage format** (also called the serialization method):
* as binary (via TBD) or
* human readable as JSON file
and **additional methods**:
* locally encrypted (see [[Local Encryption and Login]])
* shared storage that includes meta data [[Shared Storage]]
	* without encryption
	* with encryption based on [[User Registry]] 
* encrypted for remote shares (see [[User Registry]])

# Guide
## Your Functionality
Recommended is to encapsulate your functions into a class. If you want to use other ways, see the APPXF storage concept details below.
## Storage Concept
Ideally, your function is enclosed in a class that derives from APPXF Storable and forwards necessary initialization information and satisfies the interfaces. Then, when instantiating your class, you define the actual Storage behavior.