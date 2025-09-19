// API Service for AteBit Legal Document Platform
export interface ApiResponse<T = any> {
  data?: T;
  error?: string;
  status: number;
}

export interface Document {
  document_id: string;
  title: string;
  file_type: string;
  created_at: string;
  updated_at: string;
  file_size?: number;
  analysis_status?: string;
}

export interface AnalysisRequest {
  analysis_type: 'summary' | 'key_points' | 'risks' | 'translation' | 'all';
  target_language: string;
}

export interface AnalysisResult {
  analysis_type: string;
  result: any;
  created_at: string;
  token_usage?: number;
}

export class ApiService {
  private baseUrl: string;
  private token: string | null = null;

  constructor(baseUrl: string = 'http://localhost:8000') {
    this.baseUrl = baseUrl;
  }

  setToken(token: string) {
    this.token = token;
  }

  private async request<T>(
    endpoint: string, 
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseUrl}/api${endpoint}`;
    
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...options.headers as Record<string, string>,
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      const data = await response.json();

      return {
        data: response.ok ? data : undefined,
        error: response.ok ? undefined : data.detail || data.error || 'Unknown error',
        status: response.status,
      };
    } catch (error) {
      return {
        error: error instanceof Error ? error.message : 'Network error',
        status: 0,
      };
    }
  }

  // System endpoints
  async checkHealth() {
    return this.request('/health/');
  }

  async getVersion() {
    return this.request('/version/');
  }

  // Document management
  async createDocument(documentData: {
    document_id: string;
    title: string;
    file_type: string;
  }) {
    return this.request<Document>('/documents/', {
      method: 'POST',
      body: JSON.stringify(documentData),
    });
  }

  async getDocuments(limit = 20, offset = 0) {
    return this.request<{ results: Document[]; count: number }>(`/documents/?limit=${limit}&offset=${offset}`);
  }

  async getDocument(documentId: string) {
    return this.request<Document>(`/documents/${documentId}/`);
  }

  async deleteDocument(documentId: string) {
    return this.request(`/documents/${documentId}/`, {
      method: 'DELETE',
    });
  }

  // File operations
  async uploadFile(documentId: string, file: File) {
    const formData = new FormData();
    formData.append('file', file);

    const url = `${this.baseUrl}/api/documents/${documentId}/upload/`;
    const headers: Record<string, string> = {};
    
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers,
        body: formData,
      });

      const data = await response.json();

      return {
        data: response.ok ? data : undefined,
        error: response.ok ? undefined : data.detail || data.error || 'Upload failed',
        status: response.status,
      };
    } catch (error) {
      return {
        error: error instanceof Error ? error.message : 'Upload error',
        status: 0,
      };
    }
  }

  async getDownloadUrl(documentId: string) {
    return this.request<{ download_url: string }>(`/documents/${documentId}/download/`);
  }

  // AI Analysis
  async analyzeDocument(documentId: string, analysisRequest: AnalysisRequest) {
    return this.request<AnalysisResult>(`/documents/${documentId}/analyze/`, {
      method: 'POST',
      body: JSON.stringify(analysisRequest),
    });
  }

  // Utility methods
  generateDocumentId(): string {
    return crypto.randomUUID();
  }

  formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  formatDate(dateString: string): string {
    return new Date(dateString).toLocaleString();
  }
}

// Export singleton instance
export const apiService = new ApiService(
  process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
);