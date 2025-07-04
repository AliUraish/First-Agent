
import React from 'react';
import { History, Clock } from 'lucide-react';
import { HistoryEntry, Theme } from '@/pages/Index';

interface FlagHistoryProps {
  history: HistoryEntry[];
  theme: Theme;
}

export const FlagHistory: React.FC<FlagHistoryProps> = ({ history, theme }) => {
  const getActionColor = (action: HistoryEntry['action']) => {
    switch (action) {
      case 'created': return 'text-green-500';
      case 'edited': return 'text-blue-500';
      case 'reverted': return 'text-orange-500';
      default: return 'text-gray-500';
    }
  };

  const formatTime = (date: Date) => {
    return new Intl.DateTimeFormat('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      day: 'numeric',
      month: 'short'
    }).format(date);
  };

  return (
    <div className={`p-6 rounded-2xl shadow-lg h-fit ${
      theme === 'dark' ? 'bg-gray-800 border border-gray-700' : 'bg-white border border-gray-200'
    }`}>
      <h3 className="text-xl font-bold mb-4 flex items-center gap-3">
        <History className="w-5 h-5 text-purple-500" />
        Flagging History
      </h3>
      
      {history.length === 0 ? (
        <p className={`text-center py-8 ${theme === 'dark' ? 'text-gray-400' : 'text-gray-500'}`}>
          No history yet. Start flagging emails to see activity here.
        </p>
      ) : (
        <div className="space-y-4 max-h-96 overflow-y-auto">
          {history.map((entry) => (
            <div
              key={entry.id}
              className={`p-4 rounded-lg border ${
                theme === 'dark' ? 'border-gray-600' : 'border-gray-200'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className={`font-medium capitalize ${getActionColor(entry.action)}`}>
                  {entry.action}
                </span>
                <div className={`flex items-center gap-1 text-xs ${
                  theme === 'dark' ? 'text-gray-400' : 'text-gray-500'
                }`}>
                  <Clock className="w-3 h-3" />
                  {formatTime(entry.timestamp)}
                </div>
              </div>
              
              <h4 className="font-semibold text-sm mb-1">{entry.flagName}</h4>
              <p className={`text-xs ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
                {entry.details}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
