#!/usr/bin/env python
"""
Comprehensive test runner for the legal document AI backend.

This script runs all tests for the features we've developed:
- Document models (Document, Analysis, History)
- Document services (Firestore, GCS, TextExtractor)
- Document serializers (all API serializers)
- Document views (all API endpoints)
- Authentication and permissions
- Error handling and edge cases

Usage:
    python run_tests.py                    # Run all tests
    python run_tests.py --verbose          # Run with verbose output
    python run_tests.py --coverage         # Run with coverage report
    python run_tests.py --models           # Run only model tests
    python run_tests.py --services         # Run only service tests
    python run_tests.py --serializers      # Run only serializer tests
    python run_tests.py --views            # Run only view tests
"""
import os
import sys
import argparse
import django
from django.conf import settings
from django.test.utils import get_runner


def configure_django():
    """Configure Django settings for testing."""
    if not settings.configured:
        # Use the test settings module
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'test_settings')
        import test_settings
        settings.configure(**{
            attr: getattr(test_settings, attr) 
            for attr in dir(test_settings) 
            if not attr.startswith('_') and attr.isupper()
        })
    
    django.setup()


def run_tests(test_labels=None, verbosity=1, interactive=False, failfast=False, keepdb=False):
    """Run the specified tests."""
    configure_django()
    
    TestRunner = get_runner(settings)
    test_runner = TestRunner(
        verbosity=verbosity,
        interactive=interactive,
        failfast=failfast,
        keepdb=keepdb
    )
    
    if not test_labels:
        # Run all document app tests
        test_labels = [
            'apps.documents.test_models',
            'apps.documents.test_services', 
            'apps.documents.test_serializers',
            'apps.documents.test_views',
        ]
    
    failures = test_runner.run_tests(test_labels)
    return failures


def run_with_coverage(test_labels=None, verbosity=1):
    """Run tests with coverage reporting."""
    try:
        import coverage
    except ImportError:
        print("Coverage.py not installed. Install with: pip install coverage")
        return 1
    
    # Start coverage
    cov = coverage.Coverage(
        source=['apps/documents'],
        omit=[
            '*/migrations/*',
            '*/test_*.py',
            '*/tests.py',
            '*/venv/*',
            '*/env/*',
        ]
    )
    cov.start()
    
    # Run tests
    failures = run_tests(test_labels, verbosity)
    
    # Stop coverage and report
    cov.stop()
    cov.save()
    
    print("\n" + "="*50)
    print("COVERAGE REPORT")
    print("="*50)
    cov.report()
    
    # Generate HTML report
    try:
        cov.html_report(directory='htmlcov')
        print(f"\nHTML coverage report generated in: htmlcov/index.html")
    except Exception as e:
        print(f"Could not generate HTML report: {e}")
    
    return failures


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(description='Run tests for legal document AI backend')
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='Verbose output')
    parser.add_argument('--coverage', '-c', action='store_true',
                       help='Run with coverage reporting')
    parser.add_argument('--failfast', '-f', action='store_true',
                       help='Stop on first failure')
    parser.add_argument('--keepdb', '-k', action='store_true',
                       help='Keep test database')
    parser.add_argument('--interactive', '-i', action='store_true',
                       help='Interactive mode')
    
    # Test category options
    parser.add_argument('--models', action='store_true',
                       help='Run only model tests')
    parser.add_argument('--services', action='store_true',
                       help='Run only service tests')
    parser.add_argument('--serializers', action='store_true',
                       help='Run only serializer tests')
    parser.add_argument('--views', action='store_true',
                       help='Run only view tests')
    
    args = parser.parse_args()
    
    # Determine test labels based on arguments
    test_labels = None
    if args.models:
        test_labels = ['apps.documents.test_models']
    elif args.services:
        test_labels = ['apps.documents.test_services']
    elif args.serializers:
        test_labels = ['apps.documents.test_serializers']
    elif args.views:
        test_labels = ['apps.documents.test_views']
    
    verbosity = 2 if args.verbose else 1
    
    print("="*60)
    print("LEGAL DOCUMENT AI BACKEND - TEST SUITE")
    print("="*60)
    print(f"Running tests: {test_labels or 'ALL'}")
    print(f"Verbosity: {verbosity}")
    print(f"Coverage: {args.coverage}")
    print("-"*60)
    
    if args.coverage:
        failures = run_with_coverage(test_labels, verbosity)
    else:
        failures = run_tests(
            test_labels=test_labels,
            verbosity=verbosity,
            interactive=args.interactive,
            failfast=args.failfast,
            keepdb=args.keepdb
        )
    
    print("\n" + "="*60)
    if failures:
        print(f"TESTS FAILED: {failures} failure(s)")
        print("="*60)
        return 1
    else:
        print("ALL TESTS PASSED!")
        print("="*60)
        return 0


if __name__ == '__main__':
    sys.exit(main())