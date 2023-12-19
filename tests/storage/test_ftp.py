#! TODO: rename module (not just FTP). Probably "remote".

#! TODO: Test must include subfolders. (There was one article reporting DEL
#  only working on providing the full path)

#! TODO: Initialization must check obtained time deltas. This test is
#  reasonable based on unit test. But mocking CURL might get awkward.

#! TODO: Test upload and download after initialization.

#! TODO: On upload or remove: ensure file_info is updated accordingly.

#! TODO: Should keep testing FUNCTIONAL against a test FTP account. While not
#  unit testing, it covers "the real problems".
#   * credentials can come from github actions and are typically environment
#     variables
#   * for local execution, a .env file can be used and loaded via dotenv python
#     library: load_dotenv()