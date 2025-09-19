'use client';

import React, { useEffect, useState, useCallback } from 'react';
import ErrorBoundary from '../components/ErrorBoundary';
import ErrorTestingPanel from '../components/ErrorTestingPanel';
import { apiService } from '../services/api';
import { sampleDocuments, generateSampleFile, generateSamplePDF } from '../utils/sampleDocuments';

// Types
interface BackendHealth {
  status: string;
  message: string;
  version: string;
}

interface SystemStatus {
  backend: 'healthy' | 'unhealthy' | 'checking';
  backendMessage: string;
  lastChecked: Date | null;
}

interface Document {
  document_id: string;
  title: string;
  file_type: string;
  created_at: string;
  updated_at: string;
  file_size?: number;
  analysis_status?: string;
}

interface AnalysisResult {
  analysis_type: string;
  result: any;
  created_at: string;
  token_usage?: number;
}

export default function Home() {
  // System status
  const [systemStatus, setSystemStatus] = useState<SystemStatus>({
    backend: 'checking',
    backendMessage: 'Checking backend connection...',
    lastChecked: null
  });

  // Authentication
  const [firebaseToken, setFirebaseToken] = useState<string>('demo-token-for-testing');
  
  // Documents
  const [documents, setDocuments] = useState<Document[]>([]);
  const [selectedDocument, setSelectedDocument] = useState<string>('');
  
  // File upload
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadProgress, setUploadProgress] = useState<string>('');
  
  // Analysis
  const [analysisType, setAnalysisType] = useState<string>('summary');
  const [targetLanguage, setTargetLanguage] = useState<string>('en');
  const [analysisResults, setAnalysisResults] = useState<AnalysisResult[]>([]);
  const [analysisProgress, setAnalysisProgress] = useState<string>('');
  
  // UI state
  const [activeTab, setActiveTab] = useState<string>('status');
  const [isClient, setIsClient] = useState(false);

  const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  useEffect(() => {
    setIsClient(true);
    checkBackendHealth();
    // Set the API service token
    apiService.setToken(firebaseToken);
  }, []);

  useEffect(() => {
    // Update API service token when it changes
    apiService.setToken(firebaseToken);
  }, [firebaseToken]);

  // API Helper function
  const apiCall = async (endpoint: string, options: RequestInit = {}) => {
    const url = `${API_BASE}/api${endpoint}`;
    const headers = {
      'Content-Type': 'application/json',
      ...(firebaseToken && { 'Authorization': `Bearer ${firebaseToken}` }),
      ...options.headers,
    };

    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`HTTP ${response.status}: ${errorText}`);
    }

    return response.json();
  };

  // System Health Check
  const checkBackendHealth = useCallback(async () => {
    try {
      setSystemStatus(prev => ({ ...prev, backend: 'checking' }));
      
      const data = await fetch(`${API_BASE}/api/health/`).then(r => r.json());
      
      setSystemStatus({
        backend: 'healthy',
        backendMessage: `✅ ${data.message} (v${data.version})`,
        lastChecked: new Date()
      });
    } catch (error) {
      setSystemStatus({
        backend: 'unhealthy',
        backendMessage: `❌ Backend error: ${error instanceof Error ? error.message : 'Unknown error'}`,
        lastChecked: new Date()
      });
    }
  }, [API_BASE]);

  // Document Management
  const createDocument = async () => {
    try {
      const docId = crypto.randomUUID();
      const newDoc = await apiCall('/documents/', {
        method: 'POST',
        body: JSON.stringify({
          document_id: docId,
          title: `Test Document ${new Date().toLocaleTimeString()}`,
          file_type: 'application/pdf'
        })
      });
      
      setDocuments(prev => [newDoc, ...prev]);
      setSelectedDocument(docId);
      setUploadProgress(`✅ Document created: ${docId}`);
    } catch (error) {
      setUploadProgress(`❌ Error: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  };

  const loadDocuments = async () => {
    try {
      const data = await apiCall('/documents/');
      setDocuments(data.results || []);
      setUploadProgress(`✅ Loaded ${data.results?.length || 0} documents`);
    } catch (error) {
      setUploadProgress(`❌ Error loading documents: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  };

  // File Upload
  const handleFileUpload = async () => {
    if (!uploadFile || !selectedDocument) {
      setUploadProgress('❌ Please select a document and file');
      return;
    }

    try {
      setUploadProgress('📤 Uploading file...');
      
      const formData = new FormData();
      formData.append('file', uploadFile);

      const response = await fetch(`${API_BASE}/api/documents/${selectedDocument}/upload/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${firebaseToken}`,
        },
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Upload failed: ${response.statusText}`);
      }

      const result = await response.json();
      setUploadProgress(`✅ File uploaded successfully: ${result.message}`);
      setUploadFile(null);
      
      // Refresh documents list
      loadDocuments();
    } catch (error) {
      setUploadProgress(`❌ Upload error: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  };

  // AI Analysis
  const runAnalysis = async () => {
    if (!selectedDocument) {
      setAnalysisProgress('❌ Please select a document');
      return;
    }

    try {
      setAnalysisProgress(`🤖 Running ${analysisType} analysis...`);
      
      const result = await apiCall(`/documents/${selectedDocument}/analyze/`, {
        method: 'POST',
        body: JSON.stringify({
          analysis_type: analysisType,
          target_language: targetLanguage
        })
      });

      setAnalysisResults(prev => [{
        analysis_type: analysisType,
        result: result,
        created_at: new Date().toISOString(),
        token_usage: result.token_usage
      }, ...prev]);

      setAnalysisProgress(`✅ Analysis completed: ${analysisType}`);
    } catch (error) {
      setAnalysisProgress(`❌ Analysis error: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  };

  // Download Document
  const downloadDocument = async () => {
    if (!selectedDocument) {
      setUploadProgress('❌ Please select a document');
      return;
    }

    try {
      setUploadProgress('📥 Getting download URL...');
      
      const result = await apiCall(`/documents/${selectedDocument}/download/`);
      
      // Open download URL in new tab
      window.open(result.download_url, '_blank');
      setUploadProgress(`✅ Download URL generated`);
    } catch (error) {
      setUploadProgress(`❌ Download error: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  };

  const getStatusColor = (status: SystemStatus['backend']): string => {
    switch (status) {
      case 'healthy': return '#28a745';
      case 'unhealthy': return '#dc3545';
      case 'checking': return '#ffc107';
      default: return '#6c757d';
    }
  };

  const tabStyle = (tabName: string) => ({
    padding: '10px 20px',
    backgroundColor: activeTab === tabName ? '#007bff' : '#f8f9fa',
    color: activeTab === tabName ? 'white' : '#333',
    border: '1px solid #ddd',
    cursor: 'pointer',
    borderRadius: '4px 4px 0 0',
    marginRight: '5px'
  });

  return (
    <ErrorBoundary>
      <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif', maxWidth: '1400px', margin: '0 auto' }}>
        <header style={{ borderBottom: '1px solid #eee', paddingBottom: '20px', marginBottom: '20px' }}>
          <h1 style={{ color: '#333', margin: '0 0 10px 0' }}>AteBit Legal Document AI - API Testing Interface</h1>
          <p style={{ color: '#666', margin: 0 }}>🧪 Comprehensive Backend API Testing Dashboard</p>
        </header>

        {/* Tab Navigation */}
        <div style={{ marginBottom: '20px' }}>
          {['status', 'documents', 'upload', 'analysis', 'results', 'testing'].map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              style={tabStyle(tab)}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>

        {/* Status Tab */}
        {activeTab === 'status' && (
          <div style={{ padding: '20px', border: '1px solid #ddd', borderRadius: '0 8px 8px 8px' }}>
            <h2>System Status</h2>
            
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '15px', marginBottom: '20px' }}>
              <div style={{ padding: '15px', backgroundColor: '#f8f9fa', borderRadius: '6px', border: '1px solid #e9ecef' }}>
                <strong>Frontend:</strong> ✅ Running (Next.js 14.2.15, React 18.3.1)
              </div>
              <div style={{
                padding: '15px',
                backgroundColor: '#f8f9fa',
                borderRadius: '6px',
                border: '1px solid #e9ecef',
                borderLeft: `4px solid ${getStatusColor(systemStatus.backend)}`
              }}>
                <strong>Backend:</strong> {systemStatus.backendMessage}
                {systemStatus.lastChecked && isClient && (
                  <div style={{ fontSize: '12px', color: '#666', marginTop: '5px' }}>
                    Last checked: {systemStatus.lastChecked.toLocaleTimeString()}
                  </div>
                )}
              </div>
            </div>

            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                Firebase Token (for authentication):
              </label>
              <input
                type="text"
                value={firebaseToken}
                onChange={(e) => setFirebaseToken(e.target.value)}
                placeholder="Enter Firebase ID token or use demo-token-for-testing"
                style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
              />
              <small style={{ color: '#666' }}>Use "demo-token-for-testing" for development</small>
            </div>

            <button
              onClick={checkBackendHealth}
              disabled={systemStatus.backend === 'checking'}
              style={{
                padding: '10px 20px',
                backgroundColor: '#007bff',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: systemStatus.backend === 'checking' ? 'not-allowed' : 'pointer',
                opacity: systemStatus.backend === 'checking' ? 0.6 : 1
              }}
            >
              {systemStatus.backend === 'checking' ? 'Checking...' : 'Refresh Backend Status'}
            </button>

            <div style={{ marginTop: '30px' }}>
              <h3>Available API Endpoints</h3>
              <div style={{ backgroundColor: '#f8f9fa', padding: '15px', borderRadius: '4px', fontFamily: 'monospace', fontSize: '14px' }}>
                <div><strong>System:</strong></div>
                <div>GET /api/health/ - System health check</div>
                <div>GET /api/version/ - API version info</div>
                <br />
                <div><strong>Documents:</strong></div>
                <div>POST /api/documents/ - Create document</div>
                <div>GET /api/documents/ - List documents</div>
                <div>GET /api/documents/&#123;id&#125;/ - Get document</div>
                <div>DELETE /api/documents/&#123;id&#125;/ - Delete document</div>
                <br />
                <div><strong>Files:</strong></div>
                <div>POST /api/documents/&#123;id&#125;/upload/ - Upload file</div>
                <div>GET /api/documents/&#123;id&#125;/download/ - Get download URL</div>
                <br />
                <div><strong>AI Analysis:</strong></div>
                <div>POST /api/documents/&#123;id&#125;/analyze/ - Run AI analysis</div>
                <div style={{ marginLeft: '20px', color: '#666' }}>
                  Types: summary, key_points, risks, translation, all
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Documents Tab */}
        {activeTab === 'documents' && (
          <div style={{ padding: '20px', border: '1px solid #ddd', borderRadius: '0 8px 8px 8px' }}>
            <h2>Document Management</h2>
            
            <div style={{ marginBottom: '20px' }}>
              <button
                onClick={createDocument}
                style={{ padding: '10px 20px', backgroundColor: '#28a745', color: 'white', border: 'none', borderRadius: '4px', marginRight: '10px' }}
              >
                Create New Document
              </button>
              <button
                onClick={loadDocuments}
                style={{ padding: '10px 20px', backgroundColor: '#17a2b8', color: 'white', border: 'none', borderRadius: '4px' }}
              >
                Refresh Documents List
              </button>
            </div>

            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                Select Document:
              </label>
              <select
                value={selectedDocument}
                onChange={(e) => setSelectedDocument(e.target.value)}
                style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
              >
                <option value="">Select a document...</option>
                {documents.map(doc => (
                  <option key={doc.document_id} value={doc.document_id}>
                    {doc.title} ({doc.document_id.slice(0, 8)}...)
                  </option>
                ))}
              </select>
            </div>

            <div style={{ backgroundColor: '#f8f9fa', padding: '15px', borderRadius: '4px', fontFamily: 'monospace', fontSize: '14px' }}>
              {uploadProgress || 'Ready for document operations...'}
            </div>

            {documents.length > 0 && (
              <div style={{ marginTop: '20px' }}>
                <h3>Documents List:</h3>
                <div style={{ maxHeight: '300px', overflowY: 'auto', border: '1px solid #ddd', borderRadius: '4px' }}>
                  {documents.map(doc => (
                    <div
                      key={doc.document_id}
                      style={{
                        padding: '10px',
                        borderBottom: '1px solid #eee',
                        backgroundColor: selectedDocument === doc.document_id ? '#e3f2fd' : 'white'
                      }}
                    >
                      <strong>{doc.title}</strong><br />
                      <small>ID: {doc.document_id}</small><br />
                      <small>Type: {doc.file_type} | Created: {new Date(doc.created_at).toLocaleString()}</small>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Upload Tab */}
        {activeTab === 'upload' && (
          <div style={{ padding: '20px', border: '1px solid #ddd', borderRadius: '0 8px 8px 8px' }}>
            <h2>File Upload</h2>
            
            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                Selected Document:
              </label>
              <select
                value={selectedDocument}
                onChange={(e) => setSelectedDocument(e.target.value)}
                style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
              >
                <option value="">Select a document...</option>
                {documents.map(doc => (
                  <option key={doc.document_id} value={doc.document_id}>
                    {doc.title} ({doc.document_id.slice(0, 8)}...)
                  </option>
                ))}
              </select>
            </div>

            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                Choose File:
              </label>
              <input
                type="file"
                onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                accept=".pdf,.txt,.docx"
                style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px', marginBottom: '10px' }}
              />
              <small style={{ color: '#666' }}>Supported: PDF, TXT, DOCX (max 10MB)</small>
              
              <div style={{ marginTop: '15px' }}>
                <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                  Or use sample documents:
                </label>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '10px' }}>
                  {sampleDocuments.map((doc, index) => (
                    <div key={index} style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
                      <button
                        onClick={() => setUploadFile(generateSampleFile(doc))}
                        style={{
                          padding: '8px 12px',
                          backgroundColor: '#17a2b8',
                          color: 'white',
                          border: 'none',
                          borderRadius: '4px',
                          fontSize: '12px',
                          cursor: 'pointer'
                        }}
                      >
                        📄 {doc.name}
                      </button>
                      <button
                        onClick={() => setUploadFile(generateSamplePDF(doc))}
                        style={{
                          padding: '8px 12px',
                          backgroundColor: '#6f42c1',
                          color: 'white',
                          border: 'none',
                          borderRadius: '4px',
                          fontSize: '12px',
                          cursor: 'pointer'
                        }}
                      >
                        📋 PDF Version
                      </button>
                    </div>
                  ))}
                </div>
                <small style={{ color: '#666', display: 'block', marginTop: '5px' }}>
                  Click to load sample legal documents for testing
                </small>
              </div>
            </div>

            <div style={{ marginBottom: '20px' }}>
              <button
                onClick={handleFileUpload}
                disabled={!uploadFile || !selectedDocument}
                style={{
                  padding: '10px 20px',
                  backgroundColor: '#007bff',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: (!uploadFile || !selectedDocument) ? 'not-allowed' : 'pointer',
                  opacity: (!uploadFile || !selectedDocument) ? 0.6 : 1,
                  marginRight: '10px'
                }}
              >
                Upload File
              </button>
              
              <button
                onClick={downloadDocument}
                disabled={!selectedDocument}
                style={{
                  padding: '10px 20px',
                  backgroundColor: '#28a745',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: !selectedDocument ? 'not-allowed' : 'pointer',
                  opacity: !selectedDocument ? 0.6 : 1
                }}
              >
                Download Document
              </button>
            </div>

            <div style={{ backgroundColor: '#f8f9fa', padding: '15px', borderRadius: '4px', fontFamily: 'monospace', fontSize: '14px' }}>
              {uploadProgress || 'Ready for file operations...'}
            </div>
          </div>
        )}

        {/* Analysis Tab */}
        {activeTab === 'analysis' && (
          <div style={{ padding: '20px', border: '1px solid #ddd', borderRadius: '0 8px 8px 8px' }}>
            <h2>AI Analysis</h2>
            
            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                Selected Document:
              </label>
              <select
                value={selectedDocument}
                onChange={(e) => setSelectedDocument(e.target.value)}
                style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
              >
                <option value="">Select a document...</option>
                {documents.map(doc => (
                  <option key={doc.document_id} value={doc.document_id}>
                    {doc.title} ({doc.document_id.slice(0, 8)}...)
                  </option>
                ))}
              </select>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginBottom: '20px' }}>
              <div>
                <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                  Analysis Type:
                </label>
                <select
                  value={analysisType}
                  onChange={(e) => setAnalysisType(e.target.value)}
                  style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
                >
                  <option value="summary">Document Summary</option>
                  <option value="key_points">Key Points Extraction</option>
                  <option value="risks">Risk Analysis</option>
                  <option value="translation">Document Translation</option>
                  <option value="all">All Analysis Types</option>
                </select>
              </div>

              <div>
                <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                  Target Language:
                </label>
                <select
                  value={targetLanguage}
                  onChange={(e) => setTargetLanguage(e.target.value)}
                  style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
                >
                  <option value="en">English</option>
                  <option value="es">Spanish</option>
                  <option value="fr">French</option>
                  <option value="de">German</option>
                  <option value="it">Italian</option>
                  <option value="pt">Portuguese</option>
                </select>
              </div>
            </div>

            <button
              onClick={runAnalysis}
              disabled={!selectedDocument}
              style={{
                padding: '10px 20px',
                backgroundColor: '#6f42c1',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: !selectedDocument ? 'not-allowed' : 'pointer',
                opacity: !selectedDocument ? 0.6 : 1
              }}
            >
              Run Analysis
            </button>

            <div style={{ backgroundColor: '#f8f9fa', padding: '15px', borderRadius: '4px', fontFamily: 'monospace', fontSize: '14px', marginTop: '20px' }}>
              {analysisProgress || 'Ready to run AI analysis...'}
            </div>
          </div>
        )}

        {/* Results Tab */}
        {activeTab === 'results' && (
          <div style={{ padding: '20px', border: '1px solid #ddd', borderRadius: '0 8px 8px 8px' }}>
            <h2>Analysis Results</h2>
            
            {analysisResults.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '40px', color: '#666' }}>
                No analysis results yet. Run some analyses to see results here.
              </div>
            ) : (
              <div style={{ maxHeight: '600px', overflowY: 'auto' }}>
                {analysisResults.map((result, index) => (
                  <div
                    key={index}
                    style={{
                      marginBottom: '20px',
                      padding: '15px',
                      border: '1px solid #ddd',
                      borderRadius: '8px',
                      backgroundColor: '#f8f9fa'
                    }}
                  >
                    <div style={{ marginBottom: '10px' }}>
                      <strong>Analysis Type:</strong> {result.analysis_type} | 
                      <strong> Time:</strong> {new Date(result.created_at).toLocaleString()}
                      {result.token_usage && <span> | <strong>Tokens:</strong> {result.token_usage}</span>}
                    </div>
                    
                    <div style={{
                      backgroundColor: 'white',
                      padding: '15px',
                      borderRadius: '4px',
                      border: '1px solid #e9ecef',
                      fontFamily: 'monospace',
                      fontSize: '14px',
                      maxHeight: '300px',
                      overflowY: 'auto'
                    }}>
                      <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
                        {JSON.stringify(result.result, null, 2)}
                      </pre>
                    </div>
                  </div>
                ))}
              </div>
            )}
            
            {analysisResults.length > 0 && (
              <button
                onClick={() => setAnalysisResults([])}
                style={{
                  padding: '8px 16px',
                  backgroundColor: '#dc3545',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  marginTop: '10px'
                }}
              >
                Clear Results
              </button>
            )}
          </div>
        )}

        {/* Testing Tab */}
        {activeTab === 'testing' && (
          <div style={{ padding: '20px', border: '1px solid #ddd', borderRadius: '0 8px 8px 8px' }}>
            <div style={{ marginBottom: '30px' }}>
              <h2>Quick Workflow Test</h2>
              <p style={{ color: '#666', marginBottom: '15px' }}>
                Test the complete document workflow: Create → Upload → Analyze → Download
              </p>
              <button
                onClick={async () => {
                  try {
                    setUploadProgress('🚀 Starting complete workflow test...');
                    
                    // 1. Create document
                    const docId = crypto.randomUUID();
                    await apiCall('/documents/', {
                      method: 'POST',
                      body: JSON.stringify({
                        document_id: docId,
                        title: 'Workflow Test Document',
                        file_type: 'text/plain'
                      })
                    });
                    setUploadProgress('✅ Step 1: Document created');
                    
                    // 2. Upload file
                    const sampleFile = generateSampleFile(sampleDocuments[0]);
                    const formData = new FormData();
                    formData.append('file', sampleFile);
                    
                    await fetch(`${API_BASE}/api/documents/${docId}/upload/`, {
                      method: 'POST',
                      headers: { 'Authorization': `Bearer ${firebaseToken}` },
                      body: formData,
                    });
                    setUploadProgress('✅ Step 2: File uploaded');
                    
                    // 3. Run analysis
                    const analysisResult = await apiCall(`/documents/${docId}/analyze/`, {
                      method: 'POST',
                      body: JSON.stringify({
                        analysis_type: 'summary',
                        target_language: 'en'
                      })
                    });
                    setUploadProgress('✅ Step 3: Analysis completed');
                    
                    // 4. Get download URL
                    const downloadResult = await apiCall(`/documents/${docId}/download/`);
                    setUploadProgress('✅ Step 4: Download URL generated');
                    
                    // Add to results
                    setAnalysisResults(prev => [{
                      analysis_type: 'workflow_test',
                      result: {
                        document_id: docId,
                        analysis: analysisResult,
                        download_url: downloadResult.download_url,
                        workflow_status: 'completed'
                      },
                      created_at: new Date().toISOString()
                    }, ...prev]);
                    
                    setUploadProgress('🎉 Complete workflow test successful!');
                    setSelectedDocument(docId);
                    loadDocuments();
                    
                  } catch (error) {
                    setUploadProgress(`❌ Workflow test failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
                  }
                }}
                style={{
                  padding: '12px 24px',
                  backgroundColor: '#28a745',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontSize: '16px'
                }}
              >
                🧪 Run Complete Workflow Test
              </button>
            </div>
            
            <ErrorTestingPanel />
          </div>
        )}
      </div>
    </ErrorBoundary>
  );
}
