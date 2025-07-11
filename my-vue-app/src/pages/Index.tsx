import React, { useState, useEffect } from 'react';
import { Header } from '@/components/Header';
import { EmailFlagConfig } from '@/components/EmailFlagConfig';
import { ProcessingStatus, SortingProgress } from '@/components/ProcessingStatus';
import { FlagHistory } from '@/components/FlagHistory';
import { SortingHistory } from '@/components/SortingHistory';
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
    { id: '4', name: 'Junk', description: 'Marketing and promotional emails', color: '#6b7280', isActive: false },
    { id: '5', name: 'Business', description: 'Business and work-related emails', color: '#10b981', isActive: false },
];
  
const Index = () => {
  const [theme, setTheme] = useState<Theme>('light');
  const [flags, setFlags] = useState<EmailFlag[]>(defaultFlags);
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingComplete, setProcessingComplete] = useState(false);
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [userEmail, setUserEmail] = useState<string | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [sortingProgress, setSortingProgress] = useState<SortingProgress | null>(null);
  const [completionMessage, setCompletionMessage] = useState<string>('');

  // Check connection status and load user data
  const checkConnectionAndLoadData = async () => {
    console.log('🔍 Checking connection and loading data...');
    try {
      const response = await fetch('/auth/status', {
        credentials: 'include'
      });
      console.log('📡 Auth status response:', response.status);
      const data = await response.json();
      console.log('📊 Auth status data:', data);
      
      setIsConnected(data.is_connected);
      
      if (data.is_connected && data.email) {
        console.log('✅ User connected:', data.email);
        setUserEmail(data.email);
        await loadUserData(data.email);
      } else {
        console.log('❌ User not connected');
        // Reset to default state when not connected
        setUserEmail(null);
        resetToDefaults();
      }
    } catch (error) {
      console.error('❌ Failed to check connection:', error);
      setIsConnected(false);
      setUserEmail(null);
      resetToDefaults();
    }
  };

  // Load user's saved data
  const loadUserData = async (email: string) => {
    console.log('📁 Loading user data for:', email);
    try {
      const response = await fetch(`/flags/load/${email}`, {
        credentials: 'include'
      });
      console.log('📁 Load flags response:', response.status);
      const data = await response.json();
      console.log('📁 Loaded flags data:', data);
      
      if (data.flags && data.flags.length > 0) {
        setFlags(data.flags);
        console.log('✅ Loaded saved flags:', data.flags.length);
      } else {
        // If no saved data, use defaults but save them
        console.log('🔄 No saved flags, using defaults');
        setFlags(defaultFlags);
        await saveUserData(email, defaultFlags);
      }
    } catch (error) {
      console.error('❌ Failed to load user data:', error);
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
    console.log('🚀 Index component mounted, checking auth...');
    checkConnectionAndLoadData();
    
    // Check for auth success in URL
    const params = new URLSearchParams(window.location.search);
    const authParam = params.get('auth');
    const errorParam = params.get('error');
    
    console.log('🔗 URL parameters:', { auth: authParam, error: errorParam });
    
    if (authParam === 'success') {
      console.log('✅ Auth success detected in URL, redirecting...');
      // Clear the URL parameters
      window.history.replaceState({}, '', window.location.pathname);
      // Check auth status after a short delay to ensure backend has processed everything
      setTimeout(() => {
        console.log('🔄 Re-checking connection after auth success...');
        checkConnectionAndLoadData();
      }, 1000);
    } else if (errorParam) {
      console.error('❌ Auth error detected in URL:', errorParam);
      alert(`Authentication failed: ${errorParam}`);
      window.history.replaceState({}, '', window.location.pathname);
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

    if (!isConnected || !userEmail) {
      alert('Please connect to Gmail first.');
      return;
    }

    setIsProcessing(true);
    
    try {
      // Start the sorting process
      const response = await fetch('/sorting/start', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          email: userEmail,
          active_flags: activeFlags.map(flag => flag.name)
        })
      });

      if (!response.ok) {
        throw new Error(`Failed to start sorting: ${response.statusText}`);
      }

             // Poll for progress with retry mechanism
       let pollRetries = 0;
       const maxRetries = 3;
       
       const pollProgress = async () => {
         try {
           const statusResponse = await fetch(`/sorting/status/${userEmail}`, {
             credentials: 'include'
           });
           
           if (statusResponse.ok) {
             const statusData = await statusResponse.json();
             pollRetries = 0; // Reset retry counter on success
             
             if (statusData.is_processing) {
               // Update progress information
               setSortingProgress({
                 totalEmails: statusData.total_emails,
                 processedEmails: statusData.processed_emails,
                 progressPercentage: statusData.progress_percentage,
                 currentPhase: statusData.total_emails === 0 ? 'Setting up Gmail labels...' : 'Categorizing emails...'
               });
               
               // Continue polling
               setTimeout(pollProgress, 2000);
             } else {
               // Processing complete
               setSortingProgress(null);
      setIsProcessing(false);
      setProcessingComplete(true);
               
               // Set completion message based on result
               const lastSession = statusData.last_session;
               let message = `Email sorting completed with ${activeFlags.length} flag types!`;
               
               if (lastSession) {
                 if (lastSession.status === 'completed') {
                   message = `Successfully sorted ${lastSession.processed_emails}/${lastSession.total_emails} emails into categories!`;
                 } else if (lastSession.status === 'failed') {
                   message = `Sorting failed: ${lastSession.error_message || 'Unknown error occurred'}`;
                 }
               }
               setCompletionMessage(message);
      
      // Add to history
      const historyEntry: HistoryEntry = {
        id: Date.now().toString(),
        timestamp: new Date(),
                 action: 'created',  // Always show as 'created' for sorting attempts
                 flagName: 'Email Sorting',
                 details: lastSession 
                   ? lastSession.status === 'failed' 
                     ? `Sorting failed: ${lastSession.error_message || 'Unknown error'}`
                     : `Sorted ${lastSession.processed_emails}/${lastSession.total_emails} emails`
                   : `Processed emails with ${activeFlags.length} flag types`
      };
      setHistory(prev => [historyEntry, ...prev]);
      
               // Hide completion message after 4 seconds
      setTimeout(() => {
        setProcessingComplete(false);
                 setCompletionMessage('');
               }, 4000);
             }
           } else if (statusResponse.status === 401) {
             // Authentication error
             setSortingProgress(null);
             setIsProcessing(false);
             alert('Gmail connection expired during sorting. Please reconnect.');
             checkConnectionAndLoadData();
           } else {
             throw new Error(`HTTP ${statusResponse.status}: ${statusResponse.statusText}`);
           }
         } catch (error) {
           console.error('Error checking sorting status:', error);
           pollRetries++;
           
           if (pollRetries <= maxRetries) {
             // Retry after a longer delay
             setTimeout(pollProgress, 5000);
           } else {
             // Max retries reached
             setSortingProgress(null);
             setIsProcessing(false);
             alert('Lost connection to sorting service. The process may have completed. Please check your Gmail for results.');
           }
         }
       };

      // Start polling after a short delay
      setTimeout(pollProgress, 1000);

    } catch (error) {
      console.error('Error starting sort:', error);
      setSortingProgress(null);
      setIsProcessing(false);
      
      // More detailed error handling
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      if (errorMessage.includes('401')) {
        alert('Gmail connection expired. Please reconnect and try again.');
        // Trigger reconnection check
        checkConnectionAndLoadData();
      } else if (errorMessage.includes('400')) {
        alert('Invalid request. Please check your flag configuration and try again.');
      } else if (errorMessage.includes('500')) {
        alert('Server error occurred. Please try again in a few moments.');
      } else {
        alert(`Failed to start email sorting: ${errorMessage}. Please try again.`);
      }
    }
  };

  const handleRevert = async () => {
    if (!isConnected || !userEmail) {
      alert('Please connect to Gmail first.');
      return;
    }

    // Show confirmation dialog
    const confirmed = window.confirm(
      'This will remove all labels that were applied in your most recent email sorting session. This action cannot be undone. Continue?'
    );
    
    if (!confirmed) {
      return;
    }

    setIsProcessing(true);
    
    try {
      const response = await fetch(`/sorting/revert/${userEmail}`, {
        method: 'POST',
        credentials: 'include'
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      
      // Deactivate all flags in the frontend
      setFlags(prev => prev.map(flag => ({ ...flag, isActive: false })));
      
      // Add success message
      const historyEntry: HistoryEntry = {
        id: Date.now().toString(),
        timestamp: new Date(),
        action: 'reverted',
        flagName: 'Email Labels',
        details: `Started reverting labels from session ${data.session_id?.slice(0, 8)}...`
      };
      setHistory(prev => [historyEntry, ...prev]);
      
      // Show completion message
      setProcessingComplete(true);
      setCompletionMessage('Email label revert started! Labels are being removed from your emails.');
      
      // Hide completion message after 4 seconds
      setTimeout(() => {
        setProcessingComplete(false);
        setCompletionMessage('');
      }, 4000);
      
    } catch (error) {
      console.error('Error reverting email sorting:', error);
      
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      if (errorMessage.includes('404') && errorMessage.includes('No completed sorting sessions')) {
        alert('No recent email sorting sessions found to revert.');
      } else if (errorMessage.includes('401')) {
        alert('Gmail connection expired. Please reconnect and try again.');
        checkConnectionAndLoadData();
      } else {
        alert(`Failed to revert email sorting: ${errorMessage}`);
      }
    } finally {
      setIsProcessing(false);
    }
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
              progress={sortingProgress}
              completionMessage={completionMessage}
            />
          </div>

          <div className="lg:col-span-1 space-y-6">
            <FlagHistory history={history} theme={theme} />
            <SortingHistory 
              userEmail={userEmail} 
              theme={theme} 
              isConnected={isConnected} 
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default Index;
