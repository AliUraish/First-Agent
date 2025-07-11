
import React from 'react';
import { Loader2, CheckCircle } from 'lucide-react';
import { Theme } from '@/pages/Index';

export interface SortingProgress {
  totalEmails?: number;
  processedEmails?: number;
  progressPercentage?: number;
  currentPhase?: string;
}

interface ProcessingStatusProps {
  isProcessing: boolean;
  isComplete: boolean;
  theme: Theme;
  progress?: SortingProgress;
  completionMessage?: string;
}

export const ProcessingStatus: React.FC<ProcessingStatusProps> = ({ 
  isProcessing, 
  isComplete, 
  theme,
  progress,
  completionMessage
}) => {
  if (!isProcessing && !isComplete) {
    return null;
  }

  const getPhaseMessage = () => {
    if (progress?.currentPhase) {
      return progress.currentPhase;
    }
    if (progress?.totalEmails === 0) {
      return "Setting up Gmail labels...";
    }
    if (progress?.totalEmails && progress?.processedEmails) {
      return "Categorizing and labeling emails...";
    }
    return "AI agent is analyzing and flagging your emails";
  };

  return (
    <div className={`p-6 rounded-2xl shadow-lg ${
      theme === 'dark' ? 'bg-gray-800 border border-gray-700' : 'bg-white border border-gray-200'
    }`}>
      {isProcessing && (
        <div className="space-y-4">
        <div className="flex items-center justify-center space-x-4">
          <Loader2 className={`w-8 h-8 animate-spin ${theme === 'dark' ? 'text-white' : 'text-black'}`} />
            <div className="text-center">
              <h3 className="text-lg font-semibold">Sorting Emails...</h3>
            <p className={`text-sm ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
                {getPhaseMessage()}
            </p>
            </div>
          </div>
          
          {progress && progress.totalEmails !== undefined && progress.totalEmails > 0 && (
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Progress</span>
                <span>{progress.processedEmails || 0} / {progress.totalEmails}</span>
              </div>
              <div className={`w-full bg-gray-200 rounded-full h-2 ${theme === 'dark' ? 'bg-gray-700' : ''}`}>
                <div 
                  className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${progress.progressPercentage || 0}%` }}
                ></div>
              </div>
              {progress.progressPercentage !== undefined && (
                <div className="text-center text-sm">
                  {Math.round(progress.progressPercentage)}% complete
                </div>
              )}
            </div>
          )}
        </div>
      )}
      
      {isComplete && (
        <div className={`flex items-center justify-center space-x-4 ${theme === 'dark' ? 'text-white' : 'text-black'}`}>
          <CheckCircle className="w-8 h-8 text-green-500" />
          <div className="text-center">
            <h3 className="text-lg font-semibold">Sorting Complete!</h3>
            <p className={`text-sm ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
              {completionMessage || "Your emails have been successfully sorted and labeled"}
            </p>
          </div>
        </div>
      )}
    </div>
  );
};
