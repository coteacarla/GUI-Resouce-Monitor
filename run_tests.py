"""Test runner for all tests."""
import unittest
import sys
import time


def run_tests():
    """Run all tests."""
    print("\n" + "="*70)
    print("  SYSTEM RESOURCE MONITOR - TEST SUITE")
    print("="*70 + "\n")
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromName('test_main'))
    suite.addTests(loader.loadTestsFromName('test_database'))
    suite.addTests(loader.loadTestsFromName('test_gui'))
    
    print(f"Running {suite.countTestCases()} tests...\n")
    
    start_time = time.time()
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    total_time = time.time() - start_time
    
    print("\n" + "="*70)
    print("  SUMMARY")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Total time: {total_time:.2f}s")
    print("="*70 + "\n")
    
    if result.wasSuccessful():
        print("[SUCCESS] ALL TESTS PASSED\n")
    else:
        print("[FAILURE] SOME TESTS FAILED\n")
    
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    exit_code = run_tests()
    sys.exit(exit_code)
