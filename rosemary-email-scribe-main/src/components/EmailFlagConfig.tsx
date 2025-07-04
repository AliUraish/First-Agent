
import React, { useState } from 'react';
import { Flag, Edit3, Check, X } from 'lucide-react';
import { Checkbox } from '@/components/ui/checkbox';
import { EmailFlag, Theme } from '@/pages/Index';

interface EmailFlagConfigProps {
  flags: EmailFlag[];
  onFlagUpdate: (flag: EmailFlag) => void;
  theme: Theme;
}

export const EmailFlagConfig: React.FC<EmailFlagConfigProps> = ({ 
  flags, 
  onFlagUpdate, 
  theme 
}) => {
  const [editingFlag, setEditingFlag] = useState<string | null>(null);
  const [editForm, setEditForm] = useState({ name: '', description: '' });

  const handleFlagToggle = (flag: EmailFlag) => {
    onFlagUpdate({ ...flag, isActive: !flag.isActive });
  };

  const handleEditStart = (flag: EmailFlag) => {
    setEditingFlag(flag.id);
    setEditForm({ name: flag.name, description: flag.description });
  };

  const handleEditSave = (flag: EmailFlag) => {
    onFlagUpdate({ 
      ...flag, 
      name: editForm.name, 
      description: editForm.description 
    });
    setEditingFlag(null);
  };

  const handleEditCancel = () => {
    setEditingFlag(null);
    setEditForm({ name: '', description: '' });
  };

  return (
    <div className={`p-6 rounded-2xl shadow-lg ${
      theme === 'dark' ? 'bg-gray-800 border border-gray-700' : 'bg-white border border-gray-200'
    }`}>
      <h2 className="text-2xl font-bold mb-6 flex items-center gap-3">
        <Flag className={`w-6 h-6 ${theme === 'dark' ? 'text-white' : 'text-black'}`} />
        Email Flag Configuration
      </h2>
      
      <div className="grid md:grid-cols-2 gap-4">
        {flags.map((flag) => (
          <div
            key={flag.id}
            className={`p-4 rounded-xl border-2 transition-all duration-200 ${
              flag.isActive
                ? `border-2 shadow-md`
                : theme === 'dark'
                ? 'border-gray-600 hover:border-gray-500'
                : 'border-gray-200 hover:border-gray-300'
            }`}
            style={flag.isActive ? { borderColor: flag.color } : {}}
          >
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-3">
                <div
                  className="w-4 h-4 rounded-full"
                  style={{ backgroundColor: flag.color }}
                />
                {editingFlag === flag.id ? (
                  <input
                    type="text"
                    value={editForm.name}
                    onChange={(e) => setEditForm(prev => ({ ...prev, name: e.target.value }))}
                    className={`font-semibold bg-transparent border-b-2 outline-none ${
                      theme === 'dark' ? 'text-white border-white' : 'text-black border-black'
                    }`}
                    onClick={(e) => e.stopPropagation()}
                  />
                ) : (
                  <span className="font-semibold">{flag.name}</span>
                )}
              </div>
              
              <div className="flex items-center gap-2">
                {editingFlag === flag.id ? (
                  <>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleEditSave(flag);
                      }}
                      className={`p-1 rounded ${
                        theme === 'dark' ? 'text-white hover:bg-gray-700' : 'text-black hover:bg-gray-100'
                      }`}
                    >
                      <Check className="w-4 h-4" />
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleEditCancel();
                      }}
                      className={`p-1 rounded ${
                        theme === 'dark' ? 'text-white hover:bg-gray-700' : 'text-black hover:bg-gray-100'
                      }`}
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </>
                ) : (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleEditStart(flag);
                    }}
                    className={`p-1 hover:bg-gray-100 rounded ${
                      theme === 'dark' ? 'hover:bg-gray-700' : ''
                    }`}
                  >
                    <Edit3 className="w-4 h-4" />
                  </button>
                )}
                
                <Checkbox
                  checked={flag.isActive}
                  onCheckedChange={() => handleFlagToggle(flag)}
                  className={`${
                    theme === 'dark' 
                      ? 'data-[state=checked]:bg-white data-[state=checked]:border-white data-[state=checked]:text-black' 
                      : 'data-[state=checked]:bg-black data-[state=checked]:border-black'
                  }`}
                />
              </div>
            </div>
            
            {editingFlag === flag.id ? (
              <textarea
                value={editForm.description}
                onChange={(e) => setEditForm(prev => ({ ...prev, description: e.target.value }))}
                className={`w-full text-sm bg-transparent border rounded p-2 outline-none resize-none ${
                  theme === 'dark' 
                    ? 'text-gray-300 border-white' 
                    : 'text-gray-600 border-black'
                }`}
                rows={2}
                onClick={(e) => e.stopPropagation()}
              />
            ) : (
              <p className={`text-sm ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
                {flag.description}
              </p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
