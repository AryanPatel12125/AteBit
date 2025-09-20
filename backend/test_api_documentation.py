#!/usr/bin/env python
"""
API Documentation Test Script

This script validates that the API documentation examples work correctly
by testing the curl commands and API endpoints described in the documentation.
"""

import os
import sys
import requests
import json
import time
from pathlib import Path

# Configuration
API_BASE = "http://localhost:8000/api"
FIREBASE_TOKEN = "test-token-for-documentation"  # This would be a real token in practice

def test_health_endpoints():
    """Test system health endpoints."""
    print("=== Testing System Health Endpoints ===")
    
    try:
        # Test health check
        response = requests.get(f"{API_BASE}/health/", timeout=5)
        if response.status_code == 200:
            print("✓ Health check endpoint working")
            print(f"  Response: {response.json()}")
        else:
            print(f"✗ Health check failed: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"✗ Health check error: {e}")
    
    try:
        # Test version endpoint
        response = requests.get(f"{API_BASE}/version/", timeout=5)
        if response.status_code == 200:
            print("✓ Version endpoint working")
            print(f"  Response: {response.json()}")
        else:
            print(f"✗ Version endpoint failed: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"✗ Version endpoint error: {e}")

def test_authentication_required():
    """Test that authentication is required for protected endpoints."""
    print("\n=== Testing Authentication Requirements ===")
    
    # Test without authentication
    try:
        response = requests.get(f"{API_BASE}/documents/", timeout=5)
        if response.status_code == 401:
            print("✓ Authentication required (401 Unauthorized)")
        else:
            print(f"✗ Expected 401, got {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"✗ Authentication test error: {e}")
    
    # Test with invalid token
    try:
        headers = {"Authorization": "Bearer invalid-token"}
        response = requests.get(f"{API_BASE}/documents/", headers=headers, timeout=5)
        if response.status_code in [401, 403]:
            print("✓ Invalid token rejected")
        else:
            print(f"✗ Expected 401/403, got {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"✗ Invalid token test error: {e}")

def validate_api_documentation():
    """Validate API documentation completeness."""
    print("\n=== Validating API Documentation ===")
    
    # Check if documentation files exist
    doc_files = [
        "API_DOCUMENTATION.md",
        "CURL_EXAMPLES.md", 
        "FIREBASE_SETUP_GUIDE.md"
    ]
    
    for doc_file in doc_files:
        if Path(doc_file).exists():
            print(f"✓ {doc_file} exists")
            
            # Check file size
            size = Path(doc_file).stat().st_size
            if size > 1000:  # At least 1KB of content
                print(f"  - File size: {size:,} bytes")
            else:
                print(f"  - Warning: File seems small ({size} bytes)")
        else:
            print(f"✗ {doc_file} missing")
    
    # Validate API documentation structure
    api_doc_path = Path("API_DOCUMENTATION.md")
    if api_doc_path.exists():
        content = api_doc_path.read_text()
        
        # Check for required sections
        required_sections = [
            "## Overview",
            "## Authentication", 
            "## API Endpoints",
            "### Document Management",
            "### File Operations",
            "### AI Analysis",
            "## Complete Workflow Example",
            "## Firebase Configuration Setup"
        ]
        
        for section in required_sections:
            if section in content:
                print(f"✓ Documentation section: {section}")
            else:
                print(f"✗ Missing section: {section}")
        
        # Check for curl examples
        curl_count = content.count("curl -X")
        print(f"✓ Found {curl_count} curl examples")
        
        # Check for response examples
        json_count = content.count("```json")
        print(f"✓ Found {json_count} JSON response examples")

def validate_curl_examples():
    """Validate curl examples documentation."""
    print("\n=== Validating cURL Examples ===")
    
    curl_doc_path = Path("CURL_EXAMPLES.md")
    if curl_doc_path.exists():
        content = curl_doc_path.read_text()
        
        # Check for different types of examples
        example_types = [
            "System Health Checks",
            "Document Management Workflow", 
            "File Upload Examples",
            "AI Analysis Examples",
            "Error Testing Scenarios",
            "Performance Testing",
            "Integration Testing Scenarios"
        ]
        
        for example_type in example_types:
            if example_type in content:
                print(f"✓ cURL examples for: {example_type}")
            else:
                print(f"✗ Missing cURL examples for: {example_type}")
        
        # Count different HTTP methods
        methods = ["GET", "POST", "PUT", "DELETE"]
        for method in methods:
            count = content.count(f"curl -X {method}")
            if count > 0:
                print(f"✓ {method} examples: {count}")
        
        # Check for error handling examples
        error_scenarios = [
            "Authentication Errors",
            "File Upload Errors", 
            "Analysis Errors"
        ]
        
        for scenario in error_scenarios:
            if scenario in content:
                print(f"✓ Error scenario: {scenario}")

def validate_firebase_setup():
    """Validate Firebase setup guide."""
    print("\n=== Validating Firebase Setup Guide ===")
    
    firebase_doc_path = Path("FIREBASE_SETUP_GUIDE.md")
    if firebase_doc_path.exists():
        content = firebase_doc_path.read_text()
        
        # Check for setup steps
        setup_steps = [
            "Create Google Cloud Project",
            "Enable Required APIs",
            "Set Up Firebase Project", 
            "Set Up Google Cloud Storage",
            "Create Service Account",
            "Configure Vertex AI",
            "Backend Configuration",
            "Frontend Configuration",
            "Testing Configuration",
            "Security Configuration"
        ]
        
        for step in setup_steps:
            if step in content:
                print(f"✓ Setup step: {step}")
            else:
                print(f"✗ Missing setup step: {step}")
        
        # Check for code examples
        bash_count = content.count("```bash")
        python_count = content.count("```python")
        js_count = content.count("```javascript")
        
        print(f"✓ Bash examples: {bash_count}")
        print(f"✓ Python examples: {python_count}")
        print(f"✓ JavaScript examples: {js_count}")

def generate_documentation_summary():
    """Generate a summary of the documentation."""
    print("\n=== Documentation Summary ===")
    
    total_size = 0
    file_count = 0
    
    doc_files = [
        "API_DOCUMENTATION.md",
        "CURL_EXAMPLES.md",
        "FIREBASE_SETUP_GUIDE.md"
    ]
    
    for doc_file in doc_files:
        if Path(doc_file).exists():
            size = Path(doc_file).stat().st_size
            total_size += size
            file_count += 1
            
            # Count lines
            lines = len(Path(doc_file).read_text().splitlines())
            print(f"{doc_file}: {size:,} bytes, {lines:,} lines")
    
    print(f"\nTotal documentation: {file_count} files, {total_size:,} bytes")
    
    # Estimate reading time (average 200 words per minute)
    estimated_words = total_size // 5  # Rough estimate: 5 chars per word
    reading_time = estimated_words / 200
    print(f"Estimated reading time: {reading_time:.1f} minutes")

def main():
    """Main test function."""
    print("API Documentation Validation Script")
    print("=" * 50)
    
    # Test if server is running
    try:
        response = requests.get(f"{API_BASE}/health/", timeout=2)
        server_running = True
        print("✓ Backend server is running")
    except requests.exceptions.RequestException:
        server_running = False
        print("⚠ Backend server not running (some tests will be skipped)")
    
    # Run validation tests
    validate_api_documentation()
    validate_curl_examples()
    validate_firebase_setup()
    generate_documentation_summary()
    
    if server_running:
        test_health_endpoints()
        test_authentication_required()
    
    print("\n" + "=" * 50)
    print("Documentation validation completed!")
    print("\nTo start the backend server for testing:")
    print("  cd backend")
    print("  python manage.py runserver")
    print("\nTo test API endpoints with real authentication:")
    print("  1. Set up Firebase authentication")
    print("  2. Get a valid Firebase ID token")
    print("  3. Use the token in API requests")

if __name__ == "__main__":
    main()