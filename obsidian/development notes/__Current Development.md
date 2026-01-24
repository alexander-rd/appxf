# Journal
## Adapting Shared Storage and Hybrid Encryption
### Status Quo
* **Hybrid encryption** returns the **encrypted data** and the **key blobs**.
	* PublicEncryption used for the **meta files** is collecting and storing it.
	* PublicEncryption knows about to whom (roles) the storage should be encrypted ***but this is currently not set***
* **Signing** works analogously with **meta data** files

 * (+) The hybrid encryption meta file would allow to add/remove passwords *without* touching the data file itself.
	 * This is beneficial in case of large data
	 * (!) it complicates file synchronization since file state must *include* such updates
 * (/) One idea was that the updated passwords get signed again since we sign on top of the encryption. However, the correct approach is to encrypt what is signed.
### Alternative: Byte Stream
* Signature and Encryption just *alter* the bytes.

* (+) No additional files
* (-) If encryption keys are added, all files need to be touched (and re-written)
	* (+) less complexity in file handling
* (-) Upon *decrypting*, the relevant key blob must be identified unless the hybrid encryption includes ALL PUBLIC KEYS.
	* (+) compromise is to provide the key into the dictionary that was used on hybrid_encrypt.
	* (!) The general issue is that Security can perform hybrid encryption/decryption but has no knowledge about it's identity (like: user_id).

# Conclusions
* Alter security to provide the identity into hybrid_decrypt instead of needing to filter the key blob.
	* >> (++) >> This would keep key blob handling more private to Security object
* No changes to SecureSharedStorage?
	* Provide what is needed for new registry (byte stream) ***but*** ..
	* .. keep the functions for SecureSharedStorage