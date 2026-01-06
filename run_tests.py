"""Test runner for all tests."""
import unittest
import sys

if __name__ == '__main__':
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Load all tests
    suite.addTests(loader.loadTestsFromName('test_main'))
    suite.addTests(loader.loadTestsFromName('test_database'))
    suite.addTests(loader.loadTestsFromName('test_gui'))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Exit with error code if tests failed
    sys.exit(0 if result.wasSuccessful() else 1)
