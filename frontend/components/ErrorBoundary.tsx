'use client';

import React from 'react';

interface ErrorBoundaryState {
  hasError: boolean;
  error?: Error;
}

interface ErrorBoundaryProps {
  children: React.ReactNode;
  fallback?: React.ComponentType<{ error?: Error }>;
}

class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      const FallbackComponent = this.props.fallback || DefaultErrorFallback;
      return <FallbackComponent error={this.state.error} />;
    }

    return this.props.children;
  }
}

const DefaultErrorFallback: React.FC<{ error?: Error }> = ({ error }) => (
  <div style={{
    padding: '20px',
    border: '1px solid #ff6b6b',
    borderRadius: '8px',
    backgroundColor: '#ffe0e0',
    color: '#d63031',
    margin: '20px 0'
  }}>
    <h3>⚠️ Something went wrong</h3>
    <p>An error occurred while rendering this component.</p>
    {error && (
      <details style={{ marginTop: '10px' }}>
        <summary>Error details</summary>
        <pre style={{ 
          fontSize: '12px', 
          overflow: 'auto', 
          backgroundColor: '#fff',
          padding: '10px',
          borderRadius: '4px',
          marginTop: '10px'
        }}>
          {error.message}
          {error.stack && `\n\n${error.stack}`}
        </pre>
      </details>
    )}
  </div>
);

export default ErrorBoundary;