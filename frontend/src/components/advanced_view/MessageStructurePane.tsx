import { Braces, Tag } from 'lucide-react';
import React from 'react';

interface MessageStructurePaneProps {
    format: 'json' | 'tag';
    onFormatChange: (format: 'json' | 'tag') => void;
}

export const MessageStructurePane: React.FC<MessageStructurePaneProps> = ({ format, onFormatChange }) => {
    return (
        <div className="flex flex-col h-full bg-white">
            {/* Toolbar */}
            <div className="flex items-center justify-between px-3 py-2 border-b border-gray-200">
                <span className="text-sm font-medium text-gray-700">Message Structure</span>
                <div className="flex bg-gray-100 rounded p-0.5">
                    <button
                        onClick={() => onFormatChange('json')}
                        className={`px-2 py-1 text-xs font-medium rounded flex items-center gap-1.5 transition-all
                            ${format === 'json' ? 'bg-white text-blue-600 shadow-sm' : 'text-gray-500 hover:text-gray-700'}`}
                    >
                        <Braces className="w-3.5 h-3.5" />
                        JSON
                    </button>
                    <button
                        onClick={() => onFormatChange('tag')}
                        className={`px-2 py-1 text-xs font-medium rounded flex items-center gap-1.5 transition-all
                            ${format === 'tag' ? 'bg-white text-blue-600 shadow-sm' : 'text-gray-500 hover:text-gray-700'}`}
                    >
                        <Tag className="w-3.5 h-3.5" />
                        Tag
                    </button>
                </div>
            </div>

            {/* Content Area */}
            <div className="flex-1 overflow-auto p-4 font-mono text-sm">
                <div className="text-gray-400 italic">
                    {/* Placeholder for Structure Tree */}
                    Message structure will appear here...
                </div>

                {/* Example (Simulated Content) */}
                {format === 'json' ? (
                    <pre className="text-gray-800">
                        {`{
  "header": {
    "size": 112,
    "typeID": 8452145
  },
  "fields": {
    "CompanyName": "TechCorp",
    "EmployeeCount": 500
  }
}`}
                    </pre>
                ) : (
                    <div className="text-gray-800 break-all">
                        @Demo:Company|CompanyName=TechCorp|EmployeeCount=500
                    </div>
                )}
            </div>
        </div>
    );
};
