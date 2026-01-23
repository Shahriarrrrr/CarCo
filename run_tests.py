#!/usr/bin/env python
"""
Test runner script for running all backend tests
Usage:
    python run_tests.py                 # Run all tests
    python run_tests.py forum          # Run tests for specific app
    python run_tests.py --coverage     # Run with coverage report
"""

import sys
import os
import subprocess
import re
from datetime import datetime

def run_all_tests():
    """Run all tests in the project"""
    print("\n" + "=" * 80)
    print("🚀 RUNNING ALL BACKEND TESTS".center(80))
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}".center(80))
    print("=" * 80)
    
    apps = [
        'users',
        'cars',
        'parts',
        'forum',
        'payments',
        'messaging',
        'locations',
        'comments',
        'ratings',
        'notifications',
    ]
    
    test_results = []
    total_tests = 0
    total_passed = 0
    total_failed = 0
    total_errors = 0
    
    for app in apps:
        print(f"\n{'='*80}")
        print(f"📦 Testing {app.upper()} App".center(80))
        print(f"{'='*80}")
        
        # Run tests with verbose output to show individual test names
        result = subprocess.run(
            [sys.executable, 'manage.py', 'test', app, '-v', '2'],
            capture_output=True,
            text=True
        )
        
        # Print the output so user can see what's happening
        output = result.stdout + result.stderr
        print(output)
        
        # Parse test output for statistics
        test_count = 0
        failures = 0
        errors = 0
        
        # Extract test counts from output
        test_match = re.search(r'Ran (\d+) test', output)
        if test_match:
            test_count = int(test_match.group(1))
            total_tests += test_count
        
        # Check for failures and errors
        fail_match = re.search(r'FAILED \(.*?failures=(\d+)', output)
        error_match = re.search(r'errors=(\d+)', output)
        
        if fail_match:
            failures = int(fail_match.group(1))
            total_failed += failures
        if error_match:
            errors = int(error_match.group(1))
            total_errors += errors
        
        if result.returncode != 0:
            print(f"\n❌ Tests FAILED for {app} ({test_count} tests, {failures} failures, {errors} errors)")
            test_results.append({'app': app, 'status': 'FAILED', 'count': test_count, 'failures': failures, 'errors': errors})
        else:
            print(f"\n✅ Tests PASSED for {app} ({test_count} tests)")
            total_passed += test_count
            test_results.append({'app': app, 'status': 'PASSED', 'count': test_count, 'failures': 0, 'errors': 0})

    # Run integration tests
    print(f"\n{'='*80}")
    print("🔗 Running INTEGRATION TESTS".center(80))
    print(f"{'='*80}")
    
    result = subprocess.run(
        [sys.executable, 'manage.py', 'test', 'integration_tests', '-v', '2'],
        capture_output=True,
        text=True
    )
    
    # Print the output so user can see what's happening
    output = result.stdout + result.stderr
    print(output)
    
    test_count = 0
    failures = 0
    errors = 0
    
    test_match = re.search(r'Ran (\d+) test', output)
    if test_match:
        test_count = int(test_match.group(1))
        total_tests += test_count
    
    fail_match = re.search(r'FAILED \(.*?failures=(\d+)', output)
    error_match = re.search(r'errors=(\d+)', output)
    
    if fail_match:
        failures = int(fail_match.group(1))
        total_failed += failures
    if error_match:
        errors = int(error_match.group(1))
        total_errors += errors
    
    if result.returncode != 0:
        print(f"\n❌ Integration tests FAILED ({test_count} tests, {failures} failures, {errors} errors)")
        test_results.append({'app': 'integration_tests', 'status': 'FAILED', 'count': test_count, 'failures': failures, 'errors': errors})
    else:
        print(f"\n✅ Integration tests PASSED ({test_count} tests)")
        total_passed += test_count
        test_results.append({'app': 'integration_tests', 'status': 'PASSED', 'count': test_count, 'failures': 0, 'errors': 0})
    
    # Print summary
    print("\n" + "=" * 80)
    print("📊 TEST SUMMARY".center(80))
    print("=" * 80)
    
    for result in test_results:
        status_icon = "✅" if result['status'] == 'PASSED' else "❌"
        app_name = result['app'].ljust(20)
        if result['status'] == 'PASSED':
            print(f"{status_icon} {app_name} | {result['count']:3d} tests passed")
        else:
            print(f"{status_icon} {app_name} | {result['count']:3d} tests | {result['failures']} failures | {result['errors']} errors")
    
    print("\n" + "=" * 80)
    print("🏆 FINAL RESULTS".center(80))
    print("=" * 80)
    print(f"Total Tests Run:     {total_tests:3d}")
    print(f"✅ Tests Passed:     {total_passed:3d}")
    print(f"❌ Tests Failed:     {total_failed:3d}")
    print(f"⚠️  Errors:           {total_errors:3d}")
    
    success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
    print(f"\nSuccess Rate:        {success_rate:.1f}%")
    
    if total_failed == 0 and total_errors == 0:
        print("\n" + "🎉 ALL TESTS PASSED! 🎉".center(80))
    else:
        print("\n" + "⚠️  SOME TESTS FAILED - Please review the errors above ⚠️".center(80))
    
    print("=" * 80)
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}".center(80))
    print("=" * 80 + "\n")


def run_app_tests(app_name):
    """Run tests for a specific app"""
    print(f"Running tests for {app_name}...")
    result = subprocess.run([sys.executable, 'manage.py', 'test', app_name])
    sys.exit(result.returncode)


def run_with_coverage():
    """Run tests with coverage report"""
    print("Running tests with coverage...")
    
    # Check if coverage is installed
    try:
        import coverage
    except ImportError:
        print("Coverage not installed. Installing...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'coverage'])
    
    # Run coverage
    subprocess.run([sys.executable, '-m', 'coverage', 'run', '--source=.', 'manage.py', 'test'])
    subprocess.run([sys.executable, '-m', 'coverage', 'report'])
    subprocess.run([sys.executable, '-m', 'coverage', 'html'])
    print("\nHTML coverage report generated in htmlcov/index.html")


def main():
    """Main entry point"""
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        
        if arg == '--coverage' or arg == '-c':
            run_with_coverage()
        elif arg == '--help' or arg == '-h':
            print(__doc__)
        else:
            run_app_tests(arg)
    else:
        run_all_tests()


if __name__ == '__main__':
    main()
