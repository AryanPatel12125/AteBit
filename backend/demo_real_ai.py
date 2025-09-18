#!/usr/bin/env python
"""
Demo script showing real Vertex AI integration.
This replaces mock responses with actual AI analysis.
"""
import os
import sys
import django
from pathlib import Path
import asyncio

# Setup Django
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AteBit.settings')
django.setup()


async def demo_document_analysis():
    """Demo real document analysis with Vertex AI."""
    print("🤖 Legal Document AI - Real Vertex AI Demo\n")
    
    # Sample legal document
    sample_contract = """
    RENTAL AGREEMENT
    
    This rental agreement is between John Smith (Landlord) and Jane Doe (Tenant).
    
    TERMS:
    1. Monthly rent: $1,500 due on the 1st of each month
    2. Security deposit: $1,500 (refundable)
    3. Lease term: 12 months starting January 1, 2024
    4. Late fee: $50 if rent is more than 5 days late
    5. Landlord may enter with 24-hour notice for inspections
    6. No pets allowed without written permission
    7. Tenant is responsible for all utilities except water/sewer
    8. Early termination requires 60 days notice and 2 months rent penalty
    
    Both parties agree to these terms.
    """
    
    try:
        from apps.ai_services.vertex_client import VertexAIClient
        
        print("📄 Sample Document:")
        print("-" * 50)
        print(sample_contract)
        print("-" * 50)
        
        client = VertexAIClient()
        print(f"✅ Connected to Vertex AI (Project: {client.project_id})")
        
        # Test 1: Document Summarization
        print("\n🔍 1. DOCUMENT SUMMARIZATION")
        print("=" * 40)
        
        summary_result = await client.summarize_document(sample_contract)
        
        print(f"📝 Summary: {summary_result['summary']}")
        print(f"🌐 Language: {summary_result['detected_language']}")
        print(f"📊 Confidence: {summary_result['confidence']}")
        print(f"🔢 Tokens used: {summary_result['token_usage']['total_tokens']}")
        
        # Test 2: Key Points Extraction
        print("\n🎯 2. KEY POINTS EXTRACTION")
        print("=" * 40)
        
        key_points_result = await client.extract_key_points(sample_contract)
        
        for i, point in enumerate(key_points_result['key_points'], 1):
            benefit_emoji = "🏠" if point['party_benefit'] == "first_party" else "👤" if point['party_benefit'] == "opposing_party" else "🤝"
            print(f"{i}. {benefit_emoji} {point['text']}")
            print(f"   💡 {point['explanation']}")
            print(f"   📍 Benefits: {point['party_benefit']}")
            print()
        
        print(f"🔢 Tokens used: {key_points_result['token_usage']['total_tokens']}")
        
        # Test 3: Risk Analysis
        print("\n⚠️  3. RISK ANALYSIS")
        print("=" * 40)
        
        risk_result = await client.detect_risks(sample_contract)
        
        for i, risk in enumerate(risk_result['risks'], 1):
            severity_emoji = "🔴" if risk['severity'] == "HIGH" else "🟡" if risk['severity'] == "MEDIUM" else "🟢"
            print(f"{i}. {severity_emoji} {risk['severity']} RISK")
            print(f"   📋 Clause: {risk['clause']}")
            print(f"   💭 Rationale: {risk['rationale']}")
            if 'location' in risk:
                print(f"   📍 Location: {risk['location']}")
            print()
        
        summary = risk_result.get('risk_summary', {})
        print(f"📊 Risk Summary:")
        print(f"   🔴 High: {summary.get('high_risks', 0)}")
        print(f"   🟡 Medium: {summary.get('medium_risks', 0)}")
        print(f"   🟢 Low: {summary.get('low_risks', 0)}")
        print(f"   🎯 Overall: {summary.get('overall_assessment', 'N/A')}")
        print(f"🔢 Tokens used: {risk_result['token_usage']['total_tokens']}")
        
        # Test 4: Translation (Spanish)
        print("\n🌍 4. TRANSLATION TO SPANISH")
        print("=" * 40)
        
        translation_result = await client.translate_content(
            sample_contract[:500],  # Limit for demo
            target_language='es'
        )
        
        print(f"🇺🇸 Original: {translation_result['original_content'][:100]}...")
        print(f"🇪🇸 Spanish: {translation_result['translated_content'][:100]}...")
        print(f"📊 Confidence: {translation_result['confidence']}")
        print(f"🔢 Tokens used: {translation_result['token_usage']['total_tokens']}")
        
        # Calculate total cost estimate
        total_tokens = (
            summary_result['token_usage']['total_tokens'] +
            key_points_result['token_usage']['total_tokens'] +
            risk_result['token_usage']['total_tokens'] +
            translation_result['token_usage']['total_tokens']
        )
        
        # Rough cost estimate (Gemini pricing varies)
        estimated_cost = total_tokens * 0.00001  # Very rough estimate
        
        print(f"\n💰 COST ESTIMATE")
        print("=" * 40)
        print(f"🔢 Total tokens used: {total_tokens}")
        print(f"💵 Estimated cost: ${estimated_cost:.4f}")
        print("💡 Note: Actual costs may vary based on current Vertex AI pricing")
        
        print(f"\n🎉 Demo completed successfully!")
        print("Your real Vertex AI integration is working!")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        print("\n💡 Troubleshooting:")
        print("1. Run 'python test_credentials.py' to check your setup")
        print("2. Ensure your service account has Vertex AI permissions")
        print("3. Check that your project ID and credentials are correct")


async def demo_language_detection():
    """Demo language detection with different languages."""
    print("\n🌐 LANGUAGE DETECTION DEMO")
    print("=" * 40)
    
    test_texts = [
        ("English", "This is a legal contract between two parties."),
        ("Spanish", "Este es un contrato legal entre dos partes."),
        ("French", "Ceci est un contrat légal entre deux parties."),
        ("German", "Dies ist ein Rechtsvertrag zwischen zwei Parteien."),
    ]
    
    try:
        from apps.ai_services.vertex_client import VertexAIClient
        client = VertexAIClient()
        
        for expected_lang, text in test_texts:
            detected = await client.detect_language(text)
            print(f"📝 Text: {text[:50]}...")
            print(f"🎯 Expected: {expected_lang}")
            print(f"🤖 Detected: {detected}")
            print()
            
    except Exception as e:
        print(f"❌ Language detection demo failed: {e}")


if __name__ == "__main__":
    print("🚀 Starting Real Vertex AI Demo...")
    print("This will use actual Vertex AI API calls (not mocks)")
    print("Make sure your credentials are set up correctly!\n")
    
    asyncio.run(demo_document_analysis())
    asyncio.run(demo_language_detection())