# AteBit Legal Document AI Platform - cURL Examples

This document provides comprehensive cURL examples for testing all API endpoints of the AteBit Legal Document AI Platform.

## Prerequisites

Before running these examples, ensure you have:

1. **Firebase ID Token**: Obtain from your frontend authentication
2. **Backend Running**: Start the Django development server
3. **Test Files**: Prepare sample documents for upload

```bash
# Start the backend server
cd backend
python manage.py runserver

# The API will be available at: http://localhost:8000/api
```

## Environment Setup

Set up environment variables for easier testing:

```bash
# Set your Firebase ID token
export FIREBASE_TOKEN="your-firebase-id-token-here"

# Set the API base URL
export API_BASE="http://localhost:8000/api"

# Generate a test document ID
export DOC_ID=$(python -c "import uuid; print(uuid.uuid4())")
echo "Using document ID: $DOC_ID"
```

---

## 1. System Health Checks

### Check API Health

```bash
curl -X GET "$API_BASE/health/" \
  -H "Accept: application/json" \
  -w "\nStatus: %{http_code}\nTime: %{time_total}s\n"
```

### Get Version Information

```bash
curl -X GET "$API_BASE/version/" \
  -H "Accept: application/json" \
  -w "\nStatus: %{http_code}\n"
```

---

## 2. Document Management Workflow

### Create Document

```bash
# Create a new document with metadata
curl -X POST "$API_BASE/documents/" \
  -H "Authorization: Bearer $FIREBASE_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"document_id\": \"$DOC_ID\",
    \"title\": \"Sample Legal Contract\",
    \"file_type\": \"application/pdf\"
  }" \
  -w "\nStatus: %{http_code}\n" | jq '.'
```

### List All Documents

```bash
# List documents with default pagination
curl -X GET "$API_BASE/documents/" \
  -H "Authorization: Bearer $FIREBASE_TOKEN" \
  -w "\nStatus: %{http_code}\n" | jq '.'
```

### List Documents with Pagination

```bash
# List documents with custom pagination
curl -X GET "$API_BASE/documents/?limit=5&offset=0" \
  -H "Authorization: Bearer $FIREBASE_TOKEN" \
  -w "\nStatus: %{http_code}\n" | jq '.'
```

### Get Document Details

```bash
# Retrieve specific document information
curl -X GET "$API_BASE/documents/$DOC_ID/" \
  -H "Authorization: Bearer $FIREBASE_TOKEN" \
  -w "\nStatus: %{http_code}\n" | jq '.'
```

---

## 3. File Upload Examples

### Upload PDF Document

```bash
# Create a sample PDF file for testing
echo "%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj
4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
100 700 Td
(Sample Legal Document) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000206 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
300
%%EOF" > sample_contract.pdf

# Upload the PDF file
curl -X POST "$API_BASE/documents/$DOC_ID/upload/" \
  -H "Authorization: Bearer $FIREBASE_TOKEN" \
  -F "file=@sample_contract.pdf" \
  -w "\nStatus: %{http_code}\nTime: %{time_total}s\n" | jq '.'
```

### Upload Text Document

```bash
# Create a sample text document
cat > sample_agreement.txt << 'EOF'
RENTAL AGREEMENT

This rental agreement is entered into between John Doe (Tenant) and Jane Smith (Landlord).

TERMS AND CONDITIONS:

1. RENT: The monthly rent is $1,200, due on the 1st of each month.

2. SECURITY DEPOSIT: A security deposit of $1,200 is required and will be refunded at the end of the lease term if there are no damages.

3. PETS: No pets are allowed on the premises without written consent from the landlord.

4. MAINTENANCE: The tenant is responsible for basic maintenance and cleanliness.

5. TERMINATION: Either party may terminate this agreement with 30 days written notice.

6. ENTRY: The landlord may enter the premises for inspections with 24 hours notice, except in emergencies.

This agreement is governed by the laws of the State of California.

Signed:
John Doe (Tenant)
Jane Smith (Landlord)
Date: January 15, 2024
EOF

# Upload the text file
curl -X POST "$API_BASE/documents/$DOC_ID/upload/" \
  -H "Authorization: Bearer $FIREBASE_TOKEN" \
  -F "file=@sample_agreement.txt" \
  -w "\nStatus: %{http_code}\n" | jq '.'
```

### Upload Word Document (Simulated)

```bash
# For DOCX files, you would upload a real .docx file
# curl -X POST "$API_BASE/documents/$DOC_ID/upload/" \
#   -H "Authorization: Bearer $FIREBASE_TOKEN" \
#   -F "file=@sample_contract.docx" \
#   -w "\nStatus: %{http_code}\n" | jq '.'
```

---

## 4. AI Analysis Examples

### Document Summary

```bash
# Generate a plain-English summary
curl -X POST "$API_BASE/documents/$DOC_ID/analyze/" \
  -H "Authorization: Bearer $FIREBASE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "analysis_type": "summary",
    "target_language": "en"
  }' \
  -w "\nStatus: %{http_code}\nTime: %{time_total}s\n" | jq '.'
```

### Summary in Spanish

```bash
# Generate summary in Spanish
curl -X POST "$API_BASE/documents/$DOC_ID/analyze/" \
  -H "Authorization: Bearer $FIREBASE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "analysis_type": "summary",
    "target_language": "es"
  }' \
  -w "\nStatus: %{http_code}\n" | jq '.'
```

### Key Points Extraction

```bash
# Extract key points with party analysis
curl -X POST "$API_BASE/documents/$DOC_ID/analyze/" \
  -H "Authorization: Bearer $FIREBASE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "analysis_type": "key_points",
    "target_language": "en"
  }' \
  -w "\nStatus: %{http_code}\n" | jq '.'
```

### Risk Analysis

```bash
# Analyze risky clauses
curl -X POST "$API_BASE/documents/$DOC_ID/analyze/" \
  -H "Authorization: Bearer $FIREBASE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "analysis_type": "risks",
    "target_language": "en"
  }' \
  -w "\nStatus: %{http_code}\n" | jq '.'
```

### Document Translation

```bash
# Translate document to French
curl -X POST "$API_BASE/documents/$DOC_ID/analyze/" \
  -H "Authorization: Bearer $FIREBASE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "analysis_type": "translation",
    "target_language": "fr"
  }' \
  -w "\nStatus: %{http_code}\n" | jq '.'
```

### Comprehensive Analysis

```bash
# Perform all analysis types at once
curl -X POST "$API_BASE/documents/$DOC_ID/analyze/" \
  -H "Authorization: Bearer $FIREBASE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "analysis_type": "all",
    "target_language": "en"
  }' \
  -w "\nStatus: %{http_code}\nTime: %{time_total}s\n" | jq '.'
```

---

## 5. File Download

### Get Download URL

```bash
# Generate signed URL for document download
curl -X GET "$API_BASE/documents/$DOC_ID/download/" \
  -H "Authorization: Bearer $FIREBASE_TOKEN" \
  -w "\nStatus: %{http_code}\n" | jq '.'
```

### Download File Using Signed URL

```bash
# First get the download URL
DOWNLOAD_URL=$(curl -s -X GET "$API_BASE/documents/$DOC_ID/download/" \
  -H "Authorization: Bearer $FIREBASE_TOKEN" | jq -r '.download_url')

# Then download the file
curl -X GET "$DOWNLOAD_URL" \
  -o "downloaded_document.pdf" \
  -w "\nDownload Status: %{http_code}\nFile Size: %{size_download} bytes\n"
```

---

## 6. Error Testing Scenarios

### Test Authentication Errors

```bash
# Test without authentication token
curl -X GET "$API_BASE/documents/" \
  -w "\nStatus: %{http_code}\n" | jq '.'

# Test with invalid token
curl -X GET "$API_BASE/documents/" \
  -H "Authorization: Bearer invalid-token" \
  -w "\nStatus: %{http_code}\n" | jq '.'
```

### Test Invalid Document ID

```bash
# Test with malformed UUID
curl -X GET "$API_BASE/documents/invalid-uuid/" \
  -H "Authorization: Bearer $FIREBASE_TOKEN" \
  -w "\nStatus: %{http_code}\n" | jq '.'

# Test with non-existent document
FAKE_DOC_ID=$(python -c "import uuid; print(uuid.uuid4())")
curl -X GET "$API_BASE/documents/$FAKE_DOC_ID/" \
  -H "Authorization: Bearer $FIREBASE_TOKEN" \
  -w "\nStatus: %{http_code}\n" | jq '.'
```

### Test File Upload Errors

```bash
# Test file too large (create 11MB file)
dd if=/dev/zero of=large_file.pdf bs=1M count=11 2>/dev/null
curl -X POST "$API_BASE/documents/$DOC_ID/upload/" \
  -H "Authorization: Bearer $FIREBASE_TOKEN" \
  -F "file=@large_file.pdf" \
  -w "\nStatus: %{http_code}\n" | jq '.'
rm large_file.pdf

# Test unsupported file type
echo "This is not a valid document" > invalid_file.xyz
curl -X POST "$API_BASE/documents/$DOC_ID/upload/" \
  -H "Authorization: Bearer $FIREBASE_TOKEN" \
  -F "file=@invalid_file.xyz" \
  -w "\nStatus: %{http_code}\n" | jq '.'
rm invalid_file.xyz

# Test empty file
touch empty_file.pdf
curl -X POST "$API_BASE/documents/$DOC_ID/upload/" \
  -H "Authorization: Bearer $FIREBASE_TOKEN" \
  -F "file=@empty_file.pdf" \
  -w "\nStatus: %{http_code}\n" | jq '.'
rm empty_file.pdf
```

### Test Analysis Errors

```bash
# Test analysis on non-existent document
FAKE_DOC_ID=$(python -c "import uuid; print(uuid.uuid4())")
curl -X POST "$API_BASE/documents/$FAKE_DOC_ID/analyze/" \
  -H "Authorization: Bearer $FIREBASE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "analysis_type": "summary"
  }' \
  -w "\nStatus: %{http_code}\n" | jq '.'

# Test invalid analysis type
curl -X POST "$API_BASE/documents/$DOC_ID/analyze/" \
  -H "Authorization: Bearer $FIREBASE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "analysis_type": "invalid_type"
  }' \
  -w "\nStatus: %{http_code}\n" | jq '.'

# Test translation without target language
curl -X POST "$API_BASE/documents/$DOC_ID/analyze/" \
  -H "Authorization: Bearer $FIREBASE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "analysis_type": "translation"
  }' \
  -w "\nStatus: %{http_code}\n" | jq '.'

# Test unsupported language
curl -X POST "$API_BASE/documents/$DOC_ID/analyze/" \
  -H "Authorization: Bearer $FIREBASE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "analysis_type": "summary",
    "target_language": "xyz"
  }' \
  -w "\nStatus: %{http_code}\n" | jq '.'
```

---

## 7. Performance Testing

### Concurrent Requests Test

```bash
# Test multiple simultaneous requests
for i in {1..5}; do
  (
    echo "Starting request $i"
    curl -s -X GET "$API_BASE/documents/" \
      -H "Authorization: Bearer $FIREBASE_TOKEN" \
      -w "\nRequest $i Status: %{http_code} Time: %{time_total}s\n" \
      > /dev/null &
  )
done
wait
echo "All concurrent requests completed"
```

### Load Testing Script

```bash
#!/bin/bash
# Simple load test script

echo "Starting load test..."
TOTAL_REQUESTS=20
CONCURRENT_REQUESTS=5

for batch in $(seq 1 $((TOTAL_REQUESTS / CONCURRENT_REQUESTS))); do
  echo "Batch $batch of $((TOTAL_REQUESTS / CONCURRENT_REQUESTS))"
  
  for i in $(seq 1 $CONCURRENT_REQUESTS); do
    (
      curl -s -X GET "$API_BASE/health/" \
        -w "%{http_code},%{time_total}\n" \
        -o /dev/null
    ) &
  done
  
  wait
  sleep 1
done

echo "Load test completed"
```

---

## 8. Integration Testing Scenarios

### Complete Document Workflow

```bash
#!/bin/bash
# Complete workflow test script

set -e  # Exit on any error

echo "=== AteBit API Integration Test ==="

# Step 1: Create document
echo "1. Creating document..."
DOC_ID=$(python -c "import uuid; print(uuid.uuid4())")
CREATE_RESPONSE=$(curl -s -X POST "$API_BASE/documents/" \
  -H "Authorization: Bearer $FIREBASE_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"document_id\": \"$DOC_ID\",
    \"title\": \"Integration Test Document\",
    \"file_type\": \"text/plain\"
  }")

echo "Document created: $DOC_ID"

# Step 2: Upload file
echo "2. Uploading file..."
cat > integration_test.txt << 'EOF'
SOFTWARE LICENSE AGREEMENT

This Software License Agreement is between TechCorp Inc. (Licensor) and Customer (Licensee).

1. GRANT OF LICENSE
Licensor grants Licensee a non-exclusive license to use the Software.

2. RESTRICTIONS
Licensee shall not reverse engineer or distribute the Software.

3. TERMINATION
This Agreement may be terminated immediately for breach.

4. LIABILITY
Licensor shall not be liable for any damages.
EOF

UPLOAD_RESPONSE=$(curl -s -X POST "$API_BASE/documents/$DOC_ID/upload/" \
  -H "Authorization: Bearer $FIREBASE_TOKEN" \
  -F "file=@integration_test.txt")

echo "File uploaded successfully"

# Step 3: Wait for processing
echo "3. Waiting for processing..."
sleep 2

# Step 4: Perform analysis
echo "4. Analyzing document..."

# Summary
echo "  - Getting summary..."
SUMMARY_RESPONSE=$(curl -s -X POST "$API_BASE/documents/$DOC_ID/analyze/" \
  -H "Authorization: Bearer $FIREBASE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "analysis_type": "summary",
    "target_language": "en"
  }')

# Key points
echo "  - Extracting key points..."
KEY_POINTS_RESPONSE=$(curl -s -X POST "$API_BASE/documents/$DOC_ID/analyze/" \
  -H "Authorization: Bearer $FIREBASE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "analysis_type": "key_points",
    "target_language": "en"
  }')

# Risks
echo "  - Analyzing risks..."
RISKS_RESPONSE=$(curl -s -X POST "$API_BASE/documents/$DOC_ID/analyze/" \
  -H "Authorization: Bearer $FIREBASE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "analysis_type": "risks",
    "target_language": "en"
  }')

# Step 5: Get download URL
echo "5. Getting download URL..."
DOWNLOAD_RESPONSE=$(curl -s -X GET "$API_BASE/documents/$DOC_ID/download/" \
  -H "Authorization: Bearer $FIREBASE_TOKEN")

# Step 6: List documents
echo "6. Listing documents..."
LIST_RESPONSE=$(curl -s -X GET "$API_BASE/documents/" \
  -H "Authorization: Bearer $FIREBASE_TOKEN")

# Step 7: Clean up
echo "7. Cleaning up..."
DELETE_RESPONSE=$(curl -s -X DELETE "$API_BASE/documents/$DOC_ID/" \
  -H "Authorization: Bearer $FIREBASE_TOKEN" \
  -w "%{http_code}")

rm integration_test.txt

echo "=== Integration Test Completed Successfully ==="
echo "Document ID: $DOC_ID"
echo "Delete Status: $DELETE_RESPONSE"
```

### Multi-Language Testing

```bash
#!/bin/bash
# Multi-language analysis test

DOC_ID=$(python -c "import uuid; print(uuid.uuid4())")
LANGUAGES=("en" "es" "fr" "de")

echo "=== Multi-Language Analysis Test ==="

# Create and upload document
curl -s -X POST "$API_BASE/documents/" \
  -H "Authorization: Bearer $FIREBASE_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"document_id\": \"$DOC_ID\",
    \"title\": \"Multi-Language Test\",
    \"file_type\": \"text/plain\"
  }" > /dev/null

echo "This is a sample legal contract for multi-language testing." > multilang_test.txt

curl -s -X POST "$API_BASE/documents/$DOC_ID/upload/" \
  -H "Authorization: Bearer $FIREBASE_TOKEN" \
  -F "file=@multilang_test.txt" > /dev/null

sleep 2

# Test analysis in different languages
for lang in "${LANGUAGES[@]}"; do
  echo "Testing analysis in language: $lang"
  
  RESPONSE=$(curl -s -X POST "$API_BASE/documents/$DOC_ID/analyze/" \
    -H "Authorization: Bearer $FIREBASE_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{
      \"analysis_type\": \"summary\",
      \"target_language\": \"$lang\"
    }")
  
  echo "  Language: $lang - $(echo $RESPONSE | jq -r '.target_language // "error"')"
done

# Clean up
curl -s -X DELETE "$API_BASE/documents/$DOC_ID/" \
  -H "Authorization: Bearer $FIREBASE_TOKEN" > /dev/null

rm multilang_test.txt

echo "=== Multi-Language Test Completed ==="
```

---

## 9. Monitoring and Debugging

### Response Time Monitoring

```bash
# Monitor API response times
curl -X GET "$API_BASE/health/" \
  -w "DNS: %{time_namelookup}s\nConnect: %{time_connect}s\nTotal: %{time_total}s\nStatus: %{http_code}\n" \
  -o /dev/null -s
```

### Detailed Request Logging

```bash
# Enable verbose output for debugging
curl -X POST "$API_BASE/documents/$DOC_ID/analyze/" \
  -H "Authorization: Bearer $FIREBASE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "analysis_type": "summary"
  }' \
  -v \
  --trace-ascii trace.log \
  -w "\nTotal Time: %{time_total}s\nStatus: %{http_code}\n"

# View the trace log
cat trace.log
```

### Health Check Script

```bash
#!/bin/bash
# API health monitoring script

check_endpoint() {
  local endpoint=$1
  local expected_status=$2
  
  response=$(curl -s -w "%{http_code}" -X GET "$API_BASE$endpoint")
  status_code="${response: -3}"
  
  if [ "$status_code" = "$expected_status" ]; then
    echo "✓ $endpoint - OK ($status_code)"
  else
    echo "✗ $endpoint - FAIL ($status_code, expected $expected_status)"
  fi
}

echo "=== API Health Check ==="
echo "Base URL: $API_BASE"
echo "Time: $(date)"
echo

check_endpoint "/health/" "200"
check_endpoint "/version/" "200"

# Test authenticated endpoint
if [ -n "$FIREBASE_TOKEN" ]; then
  auth_response=$(curl -s -w "%{http_code}" -X GET "$API_BASE/documents/" \
    -H "Authorization: Bearer $FIREBASE_TOKEN")
  auth_status="${auth_response: -3}"
  
  if [ "$auth_status" = "200" ]; then
    echo "✓ /documents/ - OK (authenticated)"
  else
    echo "✗ /documents/ - FAIL ($auth_status)"
  fi
else
  echo "⚠ Skipping authenticated endpoints (no FIREBASE_TOKEN)"
fi

echo
echo "=== Health Check Complete ==="
```

---

## 10. Cleanup and Utilities

### Cleanup Test Data

```bash
#!/bin/bash
# Clean up test documents

echo "Cleaning up test documents..."

# Get list of documents
DOCUMENTS=$(curl -s -X GET "$API_BASE/documents/" \
  -H "Authorization: Bearer $FIREBASE_TOKEN" | jq -r '.results[].document_id')

for doc_id in $DOCUMENTS; do
  if [[ $doc_id =~ ^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$ ]]; then
    echo "Deleting document: $doc_id"
    curl -s -X DELETE "$API_BASE/documents/$doc_id/" \
      -H "Authorization: Bearer $FIREBASE_TOKEN" > /dev/null
  fi
done

echo "Cleanup completed"
```

### Generate Test Data

```bash
#!/bin/bash
# Generate test documents for development

DOCUMENT_TYPES=(
  "Rental Agreement:application/pdf"
  "Software License:text/plain"
  "Employment Contract:application/pdf"
  "Service Agreement:text/plain"
  "Privacy Policy:text/plain"
)

echo "Generating test documents..."

for doc_type in "${DOCUMENT_TYPES[@]}"; do
  IFS=':' read -r title file_type <<< "$doc_type"
  doc_id=$(python -c "import uuid; print(uuid.uuid4())")
  
  echo "Creating: $title"
  
  # Create document
  curl -s -X POST "$API_BASE/documents/" \
    -H "Authorization: Bearer $FIREBASE_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{
      \"document_id\": \"$doc_id\",
      \"title\": \"$title\",
      \"file_type\": \"$file_type\"
    }" > /dev/null
  
  # Create sample content
  echo "This is a sample $title document for testing purposes. It contains various legal terms and conditions that can be analyzed by the AI system." > "test_$doc_id.txt"
  
  # Upload file
  curl -s -X POST "$API_BASE/documents/$doc_id/upload/" \
    -H "Authorization: Bearer $FIREBASE_TOKEN" \
    -F "file=@test_$doc_id.txt" > /dev/null
  
  rm "test_$doc_id.txt"
done

echo "Test data generation completed"
```

---

## Notes

1. **jq Tool**: Many examples use `jq` for JSON formatting. Install it with:
   ```bash
   # Ubuntu/Debian
   sudo apt-get install jq
   
   # macOS
   brew install jq
   
   # Windows (with Chocolatey)
   choco install jq
   ```

2. **Environment Variables**: Set `FIREBASE_TOKEN` and `API_BASE` for easier testing:
   ```bash
   export FIREBASE_TOKEN="your-actual-firebase-token"
   export API_BASE="http://localhost:8000/api"
   ```

3. **File Permissions**: Make scripts executable:
   ```bash
   chmod +x script_name.sh
   ```

4. **Error Handling**: Add error handling to scripts:
   ```bash
   set -e  # Exit on error
   set -u  # Exit on undefined variable
   ```

5. **Rate Limiting**: Be mindful of rate limits when running multiple requests.

---

*Last updated: January 2024*
*For use with AteBit Legal Document AI Platform API v1*