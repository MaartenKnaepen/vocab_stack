"""Run all test suites."""
import sys
sys.path.insert(0, '.')

# Import all test modules
from tests.test_authentication import run_all_tests as run_auth_tests
from tests.test_leitner_algorithm import run_all_tests as run_leitner_tests
from tests.test_review_sessions import run_all_tests as run_review_tests
from tests.test_topic_operations import run_all_tests as run_topic_tests
from tests.test_data_isolation import run_all_tests as run_isolation_tests
from tests.test_admin_functions import run_all_tests as run_admin_tests


def main():
    """Run all test suites and report results."""
    print("\n" + "=" * 70)
    print(" " * 20 + "VOCAB STACK TEST SUITE")
    print("=" * 70)
    
    results = {}
    
    # Run each test suite
    test_suites = [
        ("Authentication & Authorization", run_auth_tests),
        ("Leitner Algorithm", run_leitner_tests),
        ("Review Sessions", run_review_tests),
        ("Topic Operations", run_topic_tests),
        ("Data Isolation", run_isolation_tests),
        ("Admin Functions", run_admin_tests),
    ]
    
    for name, test_func in test_suites:
        print(f"\n{'=' * 70}")
        print(f"Running: {name}")
        print(f"{'=' * 70}")
        try:
            success = test_func()
            results[name] = "PASSED" if success else "FAILED"
        except Exception as e:
            print(f"❌ Test suite crashed: {e}")
            import traceback
            traceback.print_exc()
            results[name] = "CRASHED"
    
    # Print summary
    print("\n" + "=" * 70)
    print(" " * 25 + "TEST SUMMARY")
    print("=" * 70)
    
    for name, result in results.items():
        icon = "✅" if result == "PASSED" else "❌"
        print(f"{icon} {name}: {result}")
    
    # Overall result
    passed = sum(1 for r in results.values() if r == "PASSED")
    total = len(results)
    
    print("\n" + "=" * 70)
    if passed == total:
        print(f"🎉 ALL TESTS PASSED! ({passed}/{total})")
    else:
        print(f"⚠️  SOME TESTS FAILED ({passed}/{total} passed)")
    print("=" * 70 + "\n")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
