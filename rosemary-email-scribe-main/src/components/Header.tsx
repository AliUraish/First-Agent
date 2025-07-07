
import React, { useState } from 'react';
import { Mail } from 'lucide-react';
import { Theme } from '@/pages/Index';

interface HeaderProps {
  theme: Theme;
}

export const Header: React.FC<HeaderProps> = ({ theme }) => {
  const [isGmailConnected, setIsGmailConnected] = useState(false);

  const handleGmailConnect = () => {
    // Toggle connection status for demo
    setIsGmailConnected(!isGmailConnected);
  };

  return (
    <div className="flex items-center justify-between w-full">
      <div className="flex items-center space-x-4">
        {/* Status indicator dot */}
        <div className={`w-3 h-3 rounded-full ${isGmailConnected ? 'bg-green-500' : 'bg-red-500'}`} />
        
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
        className={`px-6 py-3 rounded-lg font-medium transition-all duration-200 ${
          theme === 'dark' 
            ? 'bg-white text-black hover:bg-gray-200' 
            : 'bg-black text-white hover:bg-gray-800'
        }`}
      >
        {isGmailConnected ? 'Disconnect Gmail' : 'Connect to Gmail'}
      </button>
    </div>
  );
};
