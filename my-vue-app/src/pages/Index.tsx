import React, { useState, useEffect } from 'react';
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

const defaultFlags: EmailFlag[] = [
  { id: '1', name: 'Urgent', description: 'High priority emails', color: '#ef4444', isActive: false },
  { id: '2', name: 'Important', description: 'Important business emails', color: '#f59e0b', isActive: false },
  { id: '3', name: 'Follow-up', description: 'Emails requiring follow-up', color: '#3b82f6', isActive: false },
  { id: '4', name: 'Archive', description: 'Emails to archive', color: '#6b7280', isActive: false },
];

const Index = () => {
  const [theme, setTheme] = useState<Theme>('light');
  const [flags, setFlags] = useState<EmailFlag[]>(defaultFlags);
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingComplete, setProcessingComplete] = useState(false);
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [userEmail, setUserEmail] = useState<string | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  // Check connection status and load user data
  const checkConnectionAndLoadData = async () => {
    try {
      const response = await fetch('/auth/status', {
        credentials: 'include'
      });
      const data = await response.json();
      
      setIsConnected(data.is_connected);
      
      if (data.is_connected && data.email) {
        setUserEmail(data.email);
        await loadUserData(data.email);
      } else {
        // Reset to default state when not connected
        setUserEmail(null);
        resetToDefaults();
      }
    } catch (error) {
      console.error('Failed to check connection:', error);
      setIsConnected(false);
      setUserEmail(null);
      resetToDefaults();
    }
  };

  // Load user's saved data
  const loadUserData = async (email: string) => {
    try {
      const response = await fetch(`/flags/load/${email}`, {
        credentials: 'include'
      });
      const data = await response.json();
      
      if (data.flags && data.flags.length > 0) {
        setFlags(data.flags);
      } else {
        // If no saved data, use defaults but save them
        setFlags(defaultFlags);
        await saveUserData(email, defaultFlags);
      }
    } catch (error) {
      console.error('Failed to load user data:', error);
      setFlags(defaultFlags);
    }
  };

  // Save user's current data
  const saveUserData = async (email: string, flagsToSave: EmailFlag[]) => {
    try {
      await fetch('/flags/save', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          email,
          flags: flagsToSave
        })
      });
    } catch (error) {
      console.error('Failed to save user data:', error);
    }
  };

  // Reset UI to defaults
  const resetToDefaults = () => {
    setFlags(defaultFlags);
    setHistory([]);
    setIsProcessing(false);
    setProcessingComplete(false);
  };

  // Auto-save when flags change (if connected)
  useEffect(() => {
    if (isConnected && userEmail) {
      const timeoutId = setTimeout(() => {
        saveUserData(userEmail, flags);
      }, 1000); // Debounce saves

      return () => clearTimeout(timeoutId);
    }
  }, [flags, isConnected, userEmail]);

  // Check connection on mount and URL changes
  useEffect(() => {
    checkConnectionAndLoadData();
    
    // Check for auth success in URL
    const params = new URLSearchParams(window.location.search);
    if (params.get('auth') === 'success') {
      // Clear the URL parameters
      window.history.replaceState({}, '', window.location.pathname);
      // Check auth status after a short delay to ensure backend has processed everything
      setTimeout(checkConnectionAndLoadData, 1000);
    }
  }, []);

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
          <Header 
            theme={theme} 
            isConnected={isConnected}
            onConnectionChange={checkConnectionAndLoadData}
          />
          <SettingsDropdown 
            theme={theme} 
            onThemeChange={setTheme} 
            history={history}
          />
        </div>

        {!isConnected && (
          <div className={`mb-8 p-4 rounded-lg border-2 border-dashed ${
            theme === 'dark' ? 'border-gray-600 bg-gray-800' : 'border-gray-300 bg-gray-50'
          }`}>
            <p className={`text-center ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
              Please connect to Gmail to start using the Flag Agent
            </p>
          </div>
        )}

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
                disabled={isProcessing || !isConnected}
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
                disabled={isProcessing || !isConnected}
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
