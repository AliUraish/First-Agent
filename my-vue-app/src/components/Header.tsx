import React, { useState, useEffect } from 'react';
import { Mail } from 'lucide-react';
import { Theme } from '@/pages/Index';

interface HeaderProps {
  theme: Theme;
  isConnected?: boolean;
  onConnectionChange?: () => void;
}

export const Header: React.FC<HeaderProps> = ({ theme, isConnected = false, onConnectionChange }) => {
  const [isChecking, setIsChecking] = useState(false);

  useEffect(() => {
    // Check for auth success in URL
      const params = new URLSearchParams(window.location.search);
    if (params.get('auth') === 'success') {
        // Clear the URL parameters
        window.history.replaceState({}, '', window.location.pathname);
      // Trigger parent to check connection
      if (onConnectionChange) {
        setTimeout(onConnectionChange, 1000);
      }
    }
  }, [onConnectionChange]);

  const handleGmailConnect = async () => {
    if (isConnected) {
      // Handle disconnect
      try {
        setIsChecking(true);
        await fetch('/auth/logout', {
          method: 'POST',
          credentials: 'include'
        });
        // Trigger parent to update connection status
        if (onConnectionChange) {
          onConnectionChange();
        }
      } catch (error) {
        console.error('Failed to disconnect:', error);
      } finally {
        setIsChecking(false);
      }
    } else {
      // Handle connect - create a hidden form and submit it
      console.log('Creating form to submit to backend auth...');
      const form = document.createElement('form');
      form.method = 'GET';
      form.action = 'http://localhost:8000/auth/login';
      document.body.appendChild(form);
      form.submit();
      document.body.removeChild(form);
    }
  };

  return (
    <div className="flex items-center justify-between w-full">
      <div className="flex items-center space-x-4">
        {/* Status indicator dot */}
        <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
        
        <div className="flex items-center space-x-3">
          <div className={`p-3 rounded-xl ${theme === 'dark' ? 'bg-white' : 'bg-black'}`}>
            <Mail className={`w-8 h-8 ${theme === 'dark' ? 'text-black' : 'text-white'}`} />
          </div>
          <div>
            <h1 className={`text-4xl font-bold ${theme === 'dark' ? 'text-white' : 'text-black'}`}>
              Flag Agent
            </h1>
            <p className={`text-sm ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
              AI Email Management Agent
            </p>
          </div>
        </div>
      </div>

      {/* Gmail connection button */}
              <button
        onClick={handleGmailConnect}
        disabled={isChecking}
        className={`px-6 py-3 rounded-lg font-medium transition-all duration-200 ${
                  theme === 'dark' 
            ? 'bg-white text-black hover:bg-gray-200' 
            : 'bg-black text-white hover:bg-gray-800'
        } ${isChecking ? 'opacity-50 cursor-not-allowed' : ''}`}
      >
        {isChecking ? 'Disconnecting...' : isConnected ? 'Disconnect Gmail' : 'Connect to Gmail'}
              </button>
    </div>
  );
};
