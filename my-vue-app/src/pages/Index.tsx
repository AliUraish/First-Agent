
import React, { useState } from 'react';
import { Header } from '@/components/Header';
import { EmailFlagConfig } from '@/components/EmailFlagConfig';
import { ProcessingStatus } from '@/components/ProcessingStatus';
import { FlagHistory } from '@/components/FlagHistory';
import { SettingsDropdown } from '@/components/SettingsDropdown';

export type EmailFlag = {
  id: string;
  name: string;
  description: string;
  color: string;
  isActive: boolean;
};

export type HistoryEntry = {
  id: string;
  timestamp: Date;
  action: 'created' | 'edited' | 'reverted';
  flagName: string;
  details: string;
};

export type Theme = 'light' | 'dark';

const Index = () => {
  const [theme, setTheme] = useState<Theme>('light');
  const [flags, setFlags] = useState<EmailFlag[]>([
    { id: '1', name: 'Urgent', description: 'High priority emails', color: '#ef4444', isActive: false },
    { id: '2', name: 'Important', description: 'Important business emails', color: '#f59e0b', isActive: false },
    { id: '3', name: 'Follow-up', description: 'Emails requiring follow-up', color: '#3b82f6', isActive: false },
    { id: '4', name: 'Archive', description: 'Emails to archive', color: '#6b7280', isActive: false },
  ]);
  
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingComplete, setProcessingComplete] = useState(false);
  const [history, setHistory] = useState<HistoryEntry[]>([]);

  const handleFlagUpdate = (updatedFlag: EmailFlag) => {
    const previousFlag = flags.find(flag => flag.id === updatedFlag.id);
    
    setFlags(prev => prev.map(flag => flag.id === updatedFlag.id ? updatedFlag : flag));
    
    // Only add to history if name or description changed, not just isActive toggle
    if (previousFlag && (previousFlag.name !== updatedFlag.name || previousFlag.description !== updatedFlag.description)) {
      const historyEntry: HistoryEntry = {
        id: Date.now().toString(),
        timestamp: new Date(),
        action: 'edited',
        flagName: updatedFlag.name,
        details: `Updated ${updatedFlag.name} flag settings`
      };
      setHistory(prev => [historyEntry, ...prev]);
    }
  };

  const handleSortOut = async () => {
    const activeFlags = flags.filter(flag => flag.isActive);
    if (activeFlags.length === 0) {
      alert('Please select at least one flag type before sorting.');
      return;
    }

    setIsProcessing(true);
    
    // Simulate backend processing
    setTimeout(() => {
      setIsProcessing(false);
      setProcessingComplete(true);
      
      // Add to history
      const historyEntry: HistoryEntry = {
        id: Date.now().toString(),
        timestamp: new Date(),
        action: 'created',
        flagName: 'Batch Process',
        details: `Processed emails with ${activeFlags.length} flag types`
      };
      setHistory(prev => [historyEntry, ...prev]);
      
      // Hide completion message after 2 seconds
      setTimeout(() => {
        setProcessingComplete(false);
      }, 2000);
    }, 3000);
  };

  const handleRevert = async () => {
    setFlags(prev => prev.map(flag => ({ ...flag, isActive: false })));
    
    const historyEntry: HistoryEntry = {
      id: Date.now().toString(),
      timestamp: new Date(),
      action: 'reverted',
      flagName: 'All Flags',
      details: 'Reverted all flag settings'
    };
    setHistory(prev => [historyEntry, ...prev]);
  };

  return (
    <div className={`min-h-screen transition-colors duration-300 ${
      theme === 'dark' ? 'bg-gray-900 text-white' : 'bg-white text-gray-900'
    }`}>
      <div className="container mx-auto px-4 py-8">
        <div className="flex justify-between items-start mb-8">
          <Header theme={theme} />
          <SettingsDropdown 
            theme={theme} 
            onThemeChange={setTheme} 
            history={history}
          />
        </div>

        <div className="grid lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2 space-y-8">
            <EmailFlagConfig 
              flags={flags}
              onFlagUpdate={handleFlagUpdate}
              theme={theme}
            />
            
            <div className="flex gap-4">
              <button
                onClick={handleSortOut}
                disabled={isProcessing}
                className={`px-8 py-3 rounded-lg font-medium transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed ${
                  theme === 'dark' 
                    ? 'bg-white text-black hover:bg-gray-200' 
                    : 'bg-black text-white hover:bg-gray-800'
                }`}
              >
                {isProcessing ? 'Processing...' : 'Sort Out'}
              </button>
              
              <button
                onClick={handleRevert}
                disabled={isProcessing}
                className={`px-8 py-3 rounded-lg font-medium transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed ${
                  theme === 'dark' 
                    ? 'bg-gray-700 text-white hover:bg-gray-600 border border-gray-600' 
                    : 'bg-white text-black hover:bg-gray-100 border border-gray-300'
                }`}
              >
                Revert
              </button>
            </div>

            <ProcessingStatus 
              isProcessing={isProcessing}
              isComplete={processingComplete}
              theme={theme}
            />
          </div>

          <div className="lg:col-span-1">
            <FlagHistory history={history} theme={theme} />
          </div>
        </div>
      </div>
    </div>
  );
};

export default Index;
