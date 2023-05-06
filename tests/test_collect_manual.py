# Drafting functionality to COLLECT results of manual tests.

# The whole thing will cycle through manual/*.py. From there, it will identify:
#  1) the tested module (the first part must exist in src as *.py)
#  2) the commit with the latest update of this file (commit ID)
#  3) commit ID of latest test results
#
# Only if the test result (3) matches the latest update (2), it will mark the
# test as success and copy the .coverage for merging with pytest. Otherwise,
# the test will be marked as failure.

# Matching test file and src can become specific when applied to user libraries
# or when module layout changes. Hence, some manual configuration is
# reasonable, like:
#
# ´´´
# HelperManual(test_dir='manual', src_dir='src')
#
# def test():
#     helper_manual.check('module_name', 'manual_module_name_detail_of_test')
#     helper_manual.check('other_module', 'manual_other_module_detail')
# ´´´
#
# Coverage must then reside as: manual/.coverage.manual_module_name_detail_of_test
#
# Final coverage should then be stored as manual/.coverage


# Drafting further functionality to re-run required tests

# Like COLLECT, we will cycle through manual/*.py. Again, it needs a
# configurationon what is tested.