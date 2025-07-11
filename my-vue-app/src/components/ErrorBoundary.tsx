import React from 'react';

interface ErrorBoundaryState {
  hasError: boolean;
  error?: Error;
  errorInfo?: React.ErrorInfo;
}

interface ErrorBoundaryProps {
  children: React.ReactNode;
}

class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    // Update state so the next render will show the fallback UI
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    // Log the error details
    console.error('🚨 Error Boundary caught an error:', error);
    console.error('🚨 Error Info:', errorInfo);
    
    this.setState({
      error,
      errorInfo
    });
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50">
          <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-6">
            <div className="text-center">
              <div className="text-red-500 text-6xl mb-4">⚠️</div>
              <h1 className="text-2xl font-bold text-gray-900 mb-4">
                Something went wrong
              </h1>
              <p className="text-gray-600 mb-6">
                We're sorry, but an error occurred while loading the application.
              </p>
              
              {this.state.error && (
                <div className="bg-red-50 border border-red-200 rounded p-4 mb-4 text-left">
                  <h3 className="font-semibold text-red-800 mb-2">Error Details:</h3>
                  <p className="text-sm text-red-700 font-mono">
                    {this.state.error.message}
                  </p>
                </div>
              )}
              
              <div className="space-y-3">
                <button
                  onClick={() => window.location.reload()}
                  className="w-full bg-blue-600 text-white py-2 px-4 rounded hover:bg-blue-700 transition-colors"
                >
                  Reload Page
                </button>
                
                <button
                  onClick={() => {
                    this.setState({ hasError: false, error: undefined, errorInfo: undefined });
                  }}
                  className="w-full bg-gray-600 text-white py-2 px-4 rounded hover:bg-gray-700 transition-colors"
                >
                  Try Again
                </button>
              </div>
              
              <div className="mt-4 text-xs text-gray-500">
                Check the browser console for more detailed error information.
              </div>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary; 