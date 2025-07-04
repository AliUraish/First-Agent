
import React, { useState } from 'react';
import { Settings, Sun, Moon, History } from 'lucide-react';
import { Theme, HistoryEntry } from '@/pages/Index';

interface SettingsDropdownProps {
  theme: Theme;
  onThemeChange: (theme: Theme) => void;
  history: HistoryEntry[];
}

export const SettingsDropdown: React.FC<SettingsDropdownProps> = ({ 
  theme, 
  onThemeChange, 
  history 
}) => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`p-3 rounded-lg transition-colors ${
          theme === 'dark' 
            ? 'bg-gray-800 hover:bg-gray-700 text-white' 
            : 'bg-gray-100 hover:bg-gray-200 text-gray-800'
        }`}
      >
        <Settings className="w-5 h-5" />
      </button>
      
      {isOpen && (
        <div className={`absolute right-0 mt-2 w-64 rounded-lg shadow-lg border z-50 ${
          theme === 'dark' 
            ? 'bg-gray-800 border-gray-700' 
            : 'bg-white border-gray-200'
        }`}>
          <div className="p-4">
            <h4 className="font-semibold mb-3">Settings</h4>
            
            <div className="space-y-3">
              <div>
                <label className="text-sm font-medium mb-2 block">Theme</label>
                <div className="flex gap-2">
                  <button
                    onClick={() => onThemeChange('light')}
                    className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors ${
                      theme === 'light'
                        ? 'bg-blue-500 text-white'
                        : theme === 'dark'
                        ? 'bg-gray-700 hover:bg-gray-600'
                        : 'bg-gray-100 hover:bg-gray-200'
                    }`}
                  >
                    <Sun className="w-4 h-4" />
                    Light
                  </button>
                  <button
                    onClick={() => onThemeChange('dark')}
                    className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors ${
                      theme === 'dark'
                        ? 'bg-blue-500 text-white'
                        : 'bg-gray-100 hover:bg-gray-200 text-gray-800'
                    }`}
                  >
                    <Moon className="w-4 h-4" />
                    Dark
                  </button>
                </div>
              </div>
              
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <History className="w-4 h-4" />
                  <span className="text-sm font-medium">Recent Activity</span>
                </div>
                <div className={`text-xs p-2 rounded ${
                  theme === 'dark' ? 'bg-gray-700' : 'bg-gray-50'
                }`}>
                  {history.length > 0 ? `${history.length} recent actions` : 'No recent activity'}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
      
      {isOpen && (
        <div 
          className="fixed inset-0 z-40" 
          onClick={() => setIsOpen(false)}
        />
      )}
    </div>
  );
};
