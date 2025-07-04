
import React from 'react';
import { Mail } from 'lucide-react';
import { Theme } from '@/pages/Index';

interface HeaderProps {
  theme: Theme;
}

export const Header: React.FC<HeaderProps> = ({ theme }) => {
  return (
    <div className="flex items-center space-x-4">
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
  );
};
