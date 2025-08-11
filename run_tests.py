#!/usr/bin/env python3
"""
Test runner for Memorg system.
"""
import sys
import subprocess
import os

def run_tests():
    """Run all tests using pytest."""
    try:
        # Run pytest with coverage reporting
        result = subprocess.run([
            "poetry", "run", "pytest", 
            "-v", 
            "--tb=short",
            "tests/"
        ], cwd=os.path.dirname(__file__))
        
        return result.returncode == 0
    except FileNotFoundError:
        print("Error: Could not find poetry or pytest. Make sure they are installed.")
        return False
    except Exception as e:
        print(f"Error running tests: {e}")
        return False

if __name__ == "__main__":
    print("Running Memorg tests...")
    success = run_tests()
    
    if success:
        print("\nAll tests passed!")
        sys.exit(0)
    else:
        print("\nSome tests failed!")
        sys.exit(1)