import React, { useState, useEffect } from 'react';
import { Clock, CheckCircle, XCircle, AlertCircle, ChevronDown, ChevronUp } from 'lucide-react';
import { Theme } from '@/pages/Index';

interface SortingSession {
  session_id: string;
  start_time: string;
  end_time?: string;
  status: 'running' | 'completed' | 'failed';
  total_emails: number;
  processed_emails: number;
  flags_used: string[];
  error_message?: string;
}

interface SortingHistoryProps {
  userEmail: string | null;
  theme: Theme;
  isConnected: boolean;
}

export const SortingHistory: React.FC<SortingHistoryProps> = ({ 
  userEmail, 
  theme, 
  isConnected 
}) => {
  const [history, setHistory] = useState<SortingSession[]>([]);
  const [loading, setLoading] = useState(false);
  const [expandedSession, setExpandedSession] = useState<string | null>(null);
  const [sessionDetails, setSessionDetails] = useState<any>(null);

  const loadHistory = async () => {
    if (!userEmail || !isConnected) return;
    
    setLoading(true);
    try {
      const response = await fetch(`/sorting/history/${userEmail}`, {
        credentials: 'include'
      });
      
      if (response.ok) {
        const data = await response.json();
        setHistory(data.history || []);
      }
    } catch (error) {
      console.error('Failed to load sorting history:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadSessionDetails = async (sessionId: string) => {
    try {
      const response = await fetch(`/sorting/session/${sessionId}/details`, {
        credentials: 'include'
      });
      
      if (response.ok) {
        const data = await response.json();
        setSessionDetails(data);
      }
    } catch (error) {
      console.error('Failed to load session details:', error);
    }
  };

  const toggleSessionExpansion = (sessionId: string) => {
    if (expandedSession === sessionId) {
      setExpandedSession(null);
      setSessionDetails(null);
    } else {
      setExpandedSession(sessionId);
      loadSessionDetails(sessionId);
    }
  };

  useEffect(() => {
    loadHistory();
  }, [userEmail, isConnected]);

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'failed':
        return <XCircle className="w-4 h-4 text-red-500" />;
      case 'running':
        return <Clock className="w-4 h-4 text-blue-500" />;
      default:
        return <AlertCircle className="w-4 h-4 text-yellow-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'text-green-600 bg-green-50 border-green-200';
      case 'failed':
        return 'text-red-600 bg-red-50 border-red-200';
      case 'running':
        return 'text-blue-600 bg-blue-50 border-blue-200';
      default:
        return 'text-yellow-600 bg-yellow-50 border-yellow-200';
    }
  };

  if (!isConnected) {
    return (
      <div className={`p-4 rounded-lg ${
        theme === 'dark' ? 'bg-gray-800 text-gray-400' : 'bg-gray-50 text-gray-600'
      }`}>
        <p className="text-center text-sm">Connect to Gmail to view sorting history</p>
      </div>
    );
  }

  return (
    <div className={`space-y-4 ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">Sorting History</h3>
        <button
          onClick={loadHistory}
          disabled={loading}
          className={`px-3 py-1 text-sm rounded ${
            theme === 'dark' 
              ? 'bg-gray-700 hover:bg-gray-600 disabled:bg-gray-800' 
              : 'bg-gray-200 hover:bg-gray-300 disabled:bg-gray-100'
          } disabled:opacity-50`}
        >
          {loading ? 'Loading...' : 'Refresh'}
        </button>
      </div>

      {history.length === 0 ? (
        <div className={`p-4 rounded-lg text-center ${
          theme === 'dark' ? 'bg-gray-800 text-gray-400' : 'bg-gray-50 text-gray-600'
        }`}>
          <p className="text-sm">No sorting sessions yet</p>
          <p className="text-xs mt-1">Start sorting your emails to see history here</p>
        </div>
      ) : (
        <div className="space-y-2">
          {history.map((session) => (
            <div
              key={session.session_id}
              className={`border rounded-lg overflow-hidden ${
                theme === 'dark' ? 'border-gray-700 bg-gray-800' : 'border-gray-200 bg-white'
              }`}
            >
              <div
                className={`p-4 cursor-pointer hover:${
                  theme === 'dark' ? 'bg-gray-700' : 'bg-gray-50'
                }`}
                onClick={() => toggleSessionExpansion(session.session_id)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    {getStatusIcon(session.status)}
                    <div>
                      <div className="flex items-center space-x-2">
                        <span className="font-medium">
                          {formatDate(session.start_time)}
                        </span>
                        <span className={`px-2 py-1 text-xs rounded border ${getStatusColor(session.status)}`}>
                          {session.status}
                        </span>
                      </div>
                      <p className={`text-sm ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
                        {session.processed_emails}/{session.total_emails} emails processed
                        {session.flags_used && Array.isArray(session.flags_used) && session.flags_used.length > 0 && (
                          <span> • {session.flags_used.join(', ')}</span>
                        )}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center">
                    {expandedSession === session.session_id ? (
                      <ChevronUp className="w-4 h-4" />
                    ) : (
                      <ChevronDown className="w-4 h-4" />
                    )}
                  </div>
                </div>
              </div>

              {expandedSession === session.session_id && (
                <div className={`border-t p-4 ${
                  theme === 'dark' ? 'border-gray-700 bg-gray-900' : 'border-gray-200 bg-gray-50'
                }`}>
                  {sessionDetails ? (
                    <div className="space-y-3">
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <span className="font-medium">Session ID:</span>
                          <p className={`font-mono text-xs ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
                            {session.session_id}
                          </p>
                        </div>
                        <div>
                          <span className="font-medium">Duration:</span>
                          <p className={theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}>
                            {session.end_time 
                              ? `${Math.round((new Date(session.end_time).getTime() - new Date(session.start_time).getTime()) / 1000)}s`
                              : 'Running...'
                            }
                          </p>
                        </div>
                      </div>

                      {session.error_message && (
                        <div className="p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
                          <strong>Error:</strong> {session.error_message}
                        </div>
                      )}

                      {sessionDetails.processing_log && sessionDetails.processing_log.length > 0 && (
                        <div>
                          <h4 className="font-medium mb-2">Processing Details</h4>
                          <div className="max-h-40 overflow-y-auto space-y-1">
                            {sessionDetails.processing_log.slice(0, 10).map((log: any, index: number) => (
                              <div
                                key={index}
                                className={`text-xs p-2 rounded ${
                                  theme === 'dark' ? 'bg-gray-800' : 'bg-white'
                                }`}
                              >
                                <div className="flex items-center justify-between">
                                  <span className="font-medium truncate">
                                    {log.email_subject || 'No Subject'}
                                  </span>
                                  <span className={`px-1 py-0.5 rounded text-xs ${
                                    log.status === 'success' ? 'bg-green-100 text-green-700' :
                                    log.status === 'failed' ? 'bg-red-100 text-red-700' :
                                    'bg-gray-100 text-gray-700'
                                  }`}>
                                    {log.assigned_label || 'Unassigned'}
                                  </span>
                                </div>
                                {log.error_details && (
                                  <p className="text-red-600 mt-1">{log.error_details}</p>
                                )}
                              </div>
                            ))}
                            {sessionDetails.processing_log.length > 10 && (
                              <p className="text-xs text-center text-gray-500">
                                And {sessionDetails.processing_log.length - 10} more emails...
                              </p>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="flex items-center justify-center py-4">
                      <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500"></div>
                      <span className="ml-2 text-sm">Loading details...</span>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}; 