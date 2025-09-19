'use client';

import React, { useState } from 'react';
import { apiService } from '../services/api';

interface TestResult {
  test: string;
  status: 'success' | 'error' | 'running';
  message: string;
  timestamp: Date;
}

export default function ErrorTestingPanel() {
  const [testResults, setTestResults] = useState<TestResult[]>([]);
  const [isRunning, setIsRunning] = useState(false);

  const addResult = (test: string, status: 'success' | 'error', message: string) => {
    setTestResults(prev => [{
      test,
      status,
      message,
      timestamp: new Date()
    }, ...prev]);
  };

  const runTest = async (testName: string, testFn: () => Promise<void>) => {
    addResult(testName, 'running', 'Running test...');
    try {
      await testFn();
      addResult(testName, 'success', 'Test passed');
    } catch (error) {
      addResult(testName, 'error', error instanceof Error ? error.message : 'Test failed');
    }
  };

  const runAllErrorTests = async () => {
    setIsRunning(true);
    setTestResults([]);

    // Test 1: Invalid authentication
    await runTest('Invalid Authentication', async () => {
      const originalToken = apiService['token'];
      apiService.setToken('invalid-token-12345');
      
      const result = await apiService.getDocuments();
      if (result.status !== 401 && result.status !== 403) {
        throw new Error(`Expected 401/403, got ${result.status}`);
      }
      
      apiService.setToken(originalToken || 'demo-token-for-testing');
    });

    // Test 2: Missing authentication
    await runTest('Missing Authentication', async () => {
      const originalToken = apiService['token'];
      apiService.setToken('');
      
      const result = await apiService.getDocuments();
      if (result.status !== 401) {
        throw new Error(`Expected 401, got ${result.status}`);
      }
      
      apiService.setToken(originalToken || 'demo-token-for-testing');
    });

    // Test 3: Non-existent document
    await runTest('Non-existent Document', async () => {
      const fakeId = crypto.randomUUID();
      const result = await apiService.getDocument(fakeId);
      if (result.status !== 404) {
        throw new Error(`Expected 404, got ${result.status}`);
      }
    });

    // Test 4: Invalid document ID format
    await runTest('Invalid Document ID Format', async () => {
      const result = await apiService.getDocument('invalid-uuid-format');
      if (result.status !== 400 && result.status !== 404) {
        throw new Error(`Expected 400/404, got ${result.status}`);
      }
    });

    // Test 5: Upload to non-existent document
    await runTest('Upload to Non-existent Document', async () => {
      const fakeId = crypto.randomUUID();
      const fakeFile = new File(['test content'], 'test.txt', { type: 'text/plain' });
      
      const result = await apiService.uploadFile(fakeId, fakeFile);
      if (result.status !== 404) {
        throw new Error(`Expected 404, got ${result.status}`);
      }
    });

    // Test 6: Analyze non-existent document
    await runTest('Analyze Non-existent Document', async () => {
      const fakeId = crypto.randomUUID();
      const result = await apiService.analyzeDocument(fakeId, {
        analysis_type: 'summary',
        target_language: 'en'
      });
      if (result.status !== 404) {
        throw new Error(`Expected 404, got ${result.status}`);
      }
    });

    // Test 7: Invalid analysis type
    await runTest('Invalid Analysis Type', async () => {
      // First create a document
      const docId = crypto.randomUUID();
      await apiService.createDocument({
        document_id: docId,
        title: 'Test Document',
        file_type: 'text/plain'
      });

      // Try invalid analysis type
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/documents/${docId}/analyze/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${apiService['token'] || 'demo-token-for-testing'}`
        },
        body: JSON.stringify({
          analysis_type: 'invalid_type',
          target_language: 'en'
        })
      });

      if (response.status !== 400) {
        throw new Error(`Expected 400, got ${response.status}`);
      }
    });

    // Test 8: Invalid language code
    await runTest('Invalid Language Code', async () => {
      // Create a document first
      const docId = crypto.randomUUID();
      await apiService.createDocument({
        document_id: docId,
        title: 'Test Document',
        file_type: 'text/plain'
      });

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/documents/${docId}/analyze/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${apiService['token'] || 'demo-token-for-testing'}`
        },
        body: JSON.stringify({
          analysis_type: 'summary',
          target_language: 'invalid_lang'
        })
      });

      if (response.status !== 400) {
        throw new Error(`Expected 400, got ${response.status}`);
      }
    });

    // Test 9: Large file upload (simulate)
    await runTest('Large File Upload Test', async () => {
      // Create a document first
      const docId = crypto.randomUUID();
      await apiService.createDocument({
        document_id: docId,
        title: 'Test Document',
        file_type: 'application/pdf'
      });

      // Create a large file (11MB - should exceed limit)
      const largeContent = 'x'.repeat(11 * 1024 * 1024); // 11MB
      const largeFile = new File([largeContent], 'large_file.pdf', { type: 'application/pdf' });
      
      const result = await apiService.uploadFile(docId, largeFile);
      if (result.status !== 413 && result.status !== 400) {
        // Some servers might return 400 instead of 413
        throw new Error(`Expected 413 or 400 for large file, got ${result.status}`);
      }
    });

    // Test 10: Unsupported file type
    await runTest('Unsupported File Type', async () => {
      // Create a document first
      const docId = crypto.randomUUID();
      await apiService.createDocument({
        document_id: docId,
        title: 'Test Document',
        file_type: 'text/plain'
      });

      const unsupportedFile = new File(['test content'], 'test.xyz', { type: 'application/unknown' });
      
      const result = await apiService.uploadFile(docId, unsupportedFile);
      if (result.status !== 400 && result.status !== 415) {
        throw new Error(`Expected 400/415 for unsupported file, got ${result.status}`);
      }
    });

    setIsRunning(false);
  };

  const clearResults = () => {
    setTestResults([]);
  };

  const getStatusIcon = (status: TestResult['status']) => {
    switch (status) {
      case 'success': return '✅';
      case 'error': return '❌';
      case 'running': return '🔄';
      default: return '⚪';
    }
  };

  const getStatusColor = (status: TestResult['status']) => {
    switch (status) {
      case 'success': return '#28a745';
      case 'error': return '#dc3545';
      case 'running': return '#ffc107';
      default: return '#6c757d';
    }
  };

  return (
    <div style={{ padding: '20px', border: '1px solid #ddd', borderRadius: '8px' }}>
      <h2>Error Testing Suite</h2>
      <p style={{ color: '#666', marginBottom: '20px' }}>
        Comprehensive error scenario testing to validate API error handling and response codes.
      </p>

      <div style={{ marginBottom: '20px' }}>
        <button
          onClick={runAllErrorTests}
          disabled={isRunning}
          style={{
            padding: '10px 20px',
            backgroundColor: '#dc3545',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: isRunning ? 'not-allowed' : 'pointer',
            opacity: isRunning ? 0.6 : 1,
            marginRight: '10px'
          }}
        >
          {isRunning ? 'Running Tests...' : 'Run All Error Tests'}
        </button>

        <button
          onClick={clearResults}
          disabled={isRunning}
          style={{
            padding: '10px 20px',
            backgroundColor: '#6c757d',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: isRunning ? 'not-allowed' : 'pointer',
            opacity: isRunning ? 0.6 : 1
          }}
        >
          Clear Results
        </button>
      </div>

      {testResults.length > 0 && (
        <div style={{ maxHeight: '500px', overflowY: 'auto' }}>
          <h3>Test Results:</h3>
          {testResults.map((result, index) => (
            <div
              key={index}
              style={{
                padding: '10px',
                marginBottom: '10px',
                border: '1px solid #ddd',
                borderRadius: '4px',
                borderLeft: `4px solid ${getStatusColor(result.status)}`,
                backgroundColor: '#f8f9fa'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <strong>
                  {getStatusIcon(result.status)} {result.test}
                </strong>
                <small style={{ color: '#666' }}>
                  {result.timestamp.toLocaleTimeString()}
                </small>
              </div>
              <div style={{ marginTop: '5px', fontSize: '14px', color: '#666' }}>
                {result.message}
              </div>
            </div>
          ))}
        </div>
      )}

      {testResults.length === 0 && !isRunning && (
        <div style={{ textAlign: 'center', padding: '40px', color: '#666' }}>
          No test results yet. Click "Run All Error Tests" to start testing error scenarios.
        </div>
      )}
    </div>
  );
}