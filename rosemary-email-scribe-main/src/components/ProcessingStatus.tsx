
import React from 'react';
import { Loader2, CheckCircle } from 'lucide-react';
import { Theme } from '@/pages/Index';

interface ProcessingStatusProps {
  isProcessing: boolean;
  isComplete: boolean;
  theme: Theme;
}

export const ProcessingStatus: React.FC<ProcessingStatusProps> = ({ 
  isProcessing, 
  isComplete, 
  theme 
}) => {
  if (!isProcessing && !isComplete) {
    return null;
  }

  return (
    <div className={`p-6 rounded-2xl shadow-lg ${
      theme === 'dark' ? 'bg-gray-800 border border-gray-700' : 'bg-white border border-gray-200'
    }`}>
      {isProcessing && (
        <div className="flex items-center justify-center space-x-4">
          <Loader2 className={`w-8 h-8 animate-spin ${theme === 'dark' ? 'text-white' : 'text-black'}`} />
          <div>
            <h3 className="text-lg font-semibold">Processing Emails...</h3>
            <p className={`text-sm ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
              AI agent is analyzing and flagging your emails
            </p>
          </div>
        </div>
      )}
      
      {isComplete && (
        <div className={`flex items-center justify-center space-x-4 ${theme === 'dark' ? 'text-white' : 'text-black'}`}>
          <CheckCircle className="w-8 h-8" />
          <div>
            <h3 className="text-lg font-semibold">Processing Complete!</h3>
            <p className={`text-sm ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
              Your emails have been successfully flagged
            </p>
          </div>
        </div>
      )}
    </div>
  );
};
