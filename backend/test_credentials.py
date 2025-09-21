#!/usr/bin/env python
"""
Test script to verify GCP credentials and Vertex AI connectivity.
Run this to ensure your credentials are properly configured.
"""
import os
import sys
import django
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AteBit.settings')
django.setup()

import asyncio
from django.conf import settings


def test_environment_variables():
    """Test that required environment variables are set."""
    print("🔍 Testing environment variables...")
    
    required_vars = [
        'GOOGLE_CLOUD_PROJECT',
        'GOOGLE_APPLICATION_CREDENTIALS',
        'VERTEX_LOCATION',
        'VERTEX_MODEL_ID'
    ]
    
    missing_vars = []
    for var in required_vars:
        value = getattr(settings, var, None) or os.getenv(var)
        if not value:
            missing_vars.append(var)
        else:
            print(f"  ✅ {var}: {value}")
    
    if missing_vars:
        print(f"  ❌ Missing variables: {', '.join(missing_vars)}")
        return False
    
    print("  ✅ All environment variables are set")
    return True


def test_credentials_file():
    """Test that the credentials file exists and is readable."""
    print("\n🔍 Testing credentials file...")
    
    creds_path = getattr(settings, 'GOOGLE_APPLICATION_CREDENTIALS', '')
    if not creds_path:
        print("  ❌ GOOGLE_APPLICATION_CREDENTIALS not set")
        return False
    
    # Make path relative to backend directory
    if not os.path.isabs(creds_path):
        creds_path = os.path.join(backend_dir, creds_path)
    
    if not os.path.exists(creds_path):
        print(f"  ❌ Credentials file not found: {creds_path}")
        print(f"  💡 Please ensure the service account key is placed at: {creds_path}")
        return False
    
    try:
        with open(creds_path, 'r') as f:
            import json
            creds_data = json.load(f)
            
        if 'type' in creds_data and creds_data['type'] == 'service_account':
            print(f"  ✅ Valid service account key found: {creds_path}")
            print(f"  📧 Service account email: {creds_data.get('client_email', 'N/A')}")
            return True
        else:
            print(f"  ❌ Invalid credentials file format")
            return False
            
    except Exception as e:
        print(f"  ❌ Error reading credentials file: {e}")
        return False


def test_gcp_authentication():
    """Test GCP authentication using the credentials."""
    print("\n🔍 Testing GCP authentication...")
    
    try:
        from google.auth import default
        from google.auth.exceptions import DefaultCredentialsError
        
        credentials, project = default()
        print(f"  ✅ Successfully authenticated with GCP")
        print(f"  🏗️  Project ID: {project}")
        
        # Verify project matches settings
        expected_project = settings.GOOGLE_CLOUD_PROJECT
        if project != expected_project:
            print(f"  ⚠️  Warning: Authenticated project ({project}) differs from settings ({expected_project})")
        
        return True
        
    except DefaultCredentialsError as e:
        print(f"  ❌ Authentication failed: {e}")
        print(f"  💡 Please check your GOOGLE_APPLICATION_CREDENTIALS path")
        return False
    except Exception as e:
        print(f"  ❌ Unexpected error: {e}")
        return False


def test_vertex_ai_import():
    """Test that Vertex AI modules can be imported."""
    print("\n🔍 Testing Vertex AI imports...")
    
    try:
        import vertexai
        from vertexai.generative_models import GenerativeModel
        print("  ✅ Vertex AI modules imported successfully")
        return True
    except ImportError as e:
        print(f"  ❌ Failed to import Vertex AI modules: {e}")
        print("  💡 Please install: pip install google-cloud-aiplatform")
        return False


async def test_vertex_ai_client():
    """Test the Vertex AI client initialization and basic functionality."""
    print("\n🔍 Testing Vertex AI client...")
    
    try:
        from apps.ai_services.vertex_client import VertexAIClient
        
        # Initialize client
        client = VertexAIClient()
        print("  ✅ Vertex AI client initialized successfully")
        
        # Test basic text generation
        print("  🧪 Testing text generation...")
        test_prompt = "Explain what a legal contract is in simple terms. Respond in JSON format with a 'summary' field."
        
        response = await client._generate_text(
            test_prompt,
            max_output_tokens=100,
            temperature=0.3
        )
        
        print(f"  ✅ Text generation successful")
        print(f"  📝 Response preview: {response[:100]}...")
        
        # Try to parse as JSON
        try:
            import json
            json.loads(response)
            print("  ✅ Response is valid JSON")
        except json.JSONDecodeError:
            print("  ⚠️  Response is not valid JSON (this might be expected)")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Vertex AI client test failed: {e}")
        return False


async def test_document_analysis():
    """Test document analysis functionality."""
    print("\n🔍 Testing document analysis...")
    
    try:
        from apps.ai_services.vertex_client import VertexAIClient
        
        client = VertexAIClient()
        
        # Test document summarization
        test_document = """
        This is a simple rental agreement between John Smith (Landlord) and Jane Doe (Tenant).
        The monthly rent is $1,200 due on the first of each month.
        The security deposit is $1,200 and is refundable upon move-out if no damages.
        The lease term is 12 months starting January 1, 2024.
        """
        
        print("  🧪 Testing document summarization...")
        summary_result = await client.summarize_document(test_document)
        
        print("  ✅ Document summarization successful")
        print(f"  📊 Token usage: {summary_result.get('token_usage', {})}")
        print(f"  🌐 Detected language: {summary_result.get('detected_language', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Document analysis test failed: {e}")
        return False


async def main():
    """Run all credential and connectivity tests."""
    print("🚀 Starting GCP Credentials and Vertex AI Test\n")
    
    tests = [
        ("Environment Variables", test_environment_variables),
        ("Credentials File", test_credentials_file),
        ("GCP Authentication", test_gcp_authentication),
        ("Vertex AI Imports", test_vertex_ai_import),
        ("Vertex AI Client", test_vertex_ai_client),
        ("Document Analysis", test_document_analysis),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"  ❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*50)
    print("📋 TEST SUMMARY")
    print("="*50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n🎉 All tests passed! Your GCP credentials are properly configured.")
        print("You can now use real Vertex AI instead of mocks.")
    else:
        print("\n⚠️  Some tests failed. Please fix the issues above before proceeding.")
        print("\n💡 Common fixes:")
        print("   1. Ensure your .env file has the correct project ID")
        print("   2. Place your service account key at backend/credentials/service-account-key.json")
        print("   3. Make sure the service account has Vertex AI permissions")
        print("   4. Install required packages: pip install google-cloud-aiplatform")


if __name__ == "__main__":
    asyncio.run(main())