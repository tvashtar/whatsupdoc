#!/usr/bin/env python3
"""
Run all whatsupdoc tests in sequence.
"""

import os
import subprocess
import sys

def run_test(test_file):
    """Run a single test file and return success status."""
    print(f"\n{'='*60}")
    print(f"🧪 Running {test_file}")
    print('='*60)
    
    try:
        result = subprocess.run([
            sys.executable, f"tests/{test_file}"
        ], capture_output=False, text=True, cwd=".")
        
        if result.returncode == 0:
            print(f"✅ {test_file} PASSED")
            return True
        else:
            print(f"❌ {test_file} FAILED")
            return False
            
    except Exception as e:
        print(f"❌ {test_file} ERROR: {e}")
        return False

def main():
    print("🌟 Running all whatsupdoc tests...")
    
    # List of test files to run
    test_files = [
        "test_package_imports.py",
        "test_gcp_connection.py", 
        "test_rag_engine_connection.py",
        "test_gemini_integration.py",
        "test_slack_connection.py"
    ]
    
    results = {}
    for test_file in test_files:
        results[test_file] = run_test(test_file)
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 TEST SUMMARY")
    print('='*60)
    
    passed = sum(1 for success in results.values() if success)
    total = len(results)
    
    for test_file, success in results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status:12} {test_file}")
    
    print('-'*60)
    print(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Your whatsupdoc setup is ready!")
        return 0
    else:
        print(f"\n💥 {total - passed} test(s) failed. Please check the output above.")
        return 1

if __name__ == "__main__":
    exit(main())