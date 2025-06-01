#!/usr/bin/env python3

import sys
import os

# Add the parent directory to the path so we can import the test module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_project_areas_comprehensive import ProjectAreaTester

def main():
    """Simple test runner"""
    print("🚀 Running Energy Model Project Area Tests")
    print("=" * 60)
    
    # Create tester instance
    tester = ProjectAreaTester(base_url="http://localhost:8008/api/v1")
    
    # Run all tests
    success = tester.run_all_tests()
    
    if success:
        print("\n✅ Test suite completed!")
        sys.exit(0)
    else:
        print("\n❌ Test suite failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()