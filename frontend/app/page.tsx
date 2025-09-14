'use client';

import { useEffect, useState, useCallback } from 'react';

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

//checking file 2

export default function Home() {
  const [systemStatus, setSystemStatus] = useState<SystemStatus>({
    backend: 'checking',
    backendMessage: 'Checking backend connection...',
    lastChecked: null
  });

  const checkBackendHealth = useCallback(async () => {
    try {
      setSystemStatus(prev => ({ ...prev, backend: 'checking' }));
      
      const response = await fetch('http://localhost:8000/api/health/', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        cache: 'no-cache'
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data: BackendHealth = await response.json();
      
      setSystemStatus({
        backend: 'healthy',
        backendMessage: `✅ ${data.message} (v${data.version})`,
        lastChecked: new Date()
      });
    } catch (error) {
      console.error('Backend health check failed:', error);
      setSystemStatus({
        backend: 'unhealthy',
        backendMessage: `❌ Backend not running: ${error instanceof Error ? error.message : 'Unknown error'}`,
        lastChecked: new Date()
      });
    }
  }, []);

  useEffect(() => {
    // Initial health check
    checkBackendHealth();
    
    // Set up periodic health checks every 30 seconds
    const interval = setInterval(checkBackendHealth, 30000);
    
    // Cleanup interval on component unmount
    return () => clearInterval(interval);
  }, [checkBackendHealth]);

  const getStatusColor = (status: SystemStatus['backend']): string => {
    switch (status) {
      case 'healthy': return '#28a745';
      case 'unhealthy': return '#dc3545';
      case 'checking': return '#ffc107';
      default: return '#6c757d';
    }
  };

  return (
    <div style={{ padding: '40px', fontFamily: 'Arial, sans-serif', maxWidth: '1200px', margin: '0 auto' }}>
      <header style={{ borderBottom: '1px solid #eee', paddingBottom: '20px', marginBottom: '30px' }}>
        <h1 style={{ color: '#333', margin: '0 0 10px 0' }}>AteBit Legal Document Platform � TURBO HOT RELOAD WORKING!</h1>
                <p style={{ color: '#666', margin: '0', fontSize: '14px' }}>🚀 Turbo Hot Reload is WORKING! Change detected automatically! 🎉</p>
      </header>
      
      <section style={{ 
        marginBottom: '30px', 
        padding: '25px', 
        border: '1px solid #ddd', 
        borderRadius: '8px',
        backgroundColor: '#f8f9fa'
      }}>
        <h2 style={{ color: '#333', marginTop: 0 }}>System Status</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '15px' }}>
          <div style={{ padding: '15px', backgroundColor: 'white', borderRadius: '6px', border: '1px solid #e9ecef' }}>
            <strong>Frontend:</strong> ✅ Running (Next.js 14.2.15, React 18.3.1, TypeScript 5.6.3)
          </div>
          <div style={{ 
            padding: '15px', 
            backgroundColor: 'white', 
            borderRadius: '6px', 
            border: '1px solid #e9ecef',
            borderLeft: `4px solid ${getStatusColor(systemStatus.backend)}`
          }}>
            <strong>Backend:</strong> {systemStatus.backendMessage}
            {systemStatus.lastChecked && (
              <div style={{ fontSize: '12px', color: '#666', marginTop: '5px' }}>
                Last checked: {systemStatus.lastChecked.toLocaleTimeString()}
              </div>
            )}
          </div>
        </div>
        <button 
          onClick={checkBackendHealth}
          disabled={systemStatus.backend === 'checking'}
          style={{
            marginTop: '15px',
            padding: '8px 16px',
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
      </section>
      
      <section style={{ marginBottom: '30px' }}>
        <h2 style={{ color: '#333' }}>Team Starting Points</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(350px, 1fr))', gap: '20px' }}>
          <div style={{ padding: '20px', border: '1px solid #ddd', borderRadius: '8px' }}>
            <h3 style={{ color: '#007bff', marginTop: 0 }}>🔧 Backend Team</h3>
            <ul style={{ marginBottom: 0 }}>
              <li><strong>Models:</strong> <code>/backend/apps/*/models.py</code></li>
              <li><strong>APIs:</strong> <code>/backend/apps/*/views.py</code></li>
              <li><strong>Settings:</strong> <code>/backend/AteBit/settings.py</code></li>
              <li><strong>URLs:</strong> <code>/backend/AteBit/urls.py</code></li>
            </ul>
          </div>
          
          <div style={{ padding: '20px', border: '1px solid #ddd', borderRadius: '8px' }}>
            <h3 style={{ color: '#28a745', marginTop: 0 }}>🎨 Frontend Team</h3>
            <ul style={{ marginBottom: 0 }}>
              <li><strong>Components:</strong> <code>/frontend/components/</code></li>
              <li><strong>Pages:</strong> <code>/frontend/app/</code></li>
              <li><strong>Services:</strong> <code>/frontend/services/</code></li>
              <li><strong>Types:</strong> Full TypeScript support enabled</li>
            </ul>
          </div>
          
          <div style={{ padding: '20px', border: '1px solid #ddd', borderRadius: '8px' }}>
            <h3 style={{ color: '#6f42c1', marginTop: 0 }}>🗄️ Database Team</h3>
            <ul style={{ marginBottom: 0 }}>
              <li><strong>Schema:</strong> <code>/backend/apps/*/models.py</code></li>
              <li><strong>Migrations:</strong> <code>python manage.py makemigrations</code></li>
              <li><strong>Admin:</strong> <code>/backend/apps/*/admin.py</code></li>
              <li><strong>Seeds:</strong> Ready for fixtures</li>
            </ul>
          </div>
        </div>
      </section>
      
      <section style={{ marginBottom: '30px' }}>
        <h2 style={{ color: '#333' }}>Development Commands</h2>
        <div style={{ backgroundColor: '#f8f9fa', padding: '20px', borderRadius: '8px', fontFamily: 'monospace' }}>
          <div style={{ marginBottom: '10px' }}><strong>Start:</strong> <code>docker-compose up --build</code></div>
          <div style={{ marginBottom: '10px' }}><strong>Logs:</strong> <code>docker-compose logs backend frontend</code></div>
          <div style={{ marginBottom: '10px' }}><strong>Shell:</strong> <code>docker-compose exec backend bash</code></div>
          <div><strong>Stop:</strong> <code>docker-compose down</code></div>
        </div>
      </section>
      
      <footer style={{ 
        borderTop: '1px solid #eee', 
        paddingTop: '20px', 
        fontSize: '14px', 
        color: '#666',
        textAlign: 'center'
      }}>
        <p>🚀 <strong>Ready for Complex Development:</strong> Advanced React patterns, TypeScript, async operations, and production-grade error handling all supported!</p>
        <p><em>TODO: This is infrastructure-only boilerplate - implement your legal document AI features here</em></p>
      </footer>
    </div>
  );
}
