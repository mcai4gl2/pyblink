// Schema Editor Component using Monaco Editor

import Editor from '@monaco-editor/react';
import { AlertCircle, CheckCircle2 } from 'lucide-react';
import React from 'react';

interface SchemaEditorProps {
    value: string;
    onChange: (value: string) => void;
    onValidate?: () => void;
    error?: string;
    isValid?: boolean;
}

export const SchemaEditor: React.FC<SchemaEditorProps> = ({
    value,
    onChange,
    onValidate,
    error,
    isValid,
}) => {
    return (
        <div className="flex flex-col h-full">
            <div className="flex items-center justify-between mb-2">
                <h2 className="text-lg font-semibold text-gray-800">Schema Definition</h2>
                <button
                    onClick={onValidate}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors text-sm font-medium"
                >
                    Validate Schema
                </button>
            </div>

            <div className="flex-1 border border-gray-300 rounded-md overflow-hidden">
                <Editor
                    height="100%"
                    defaultLanguage="plaintext"
                    value={value}
                    onChange={(value) => onChange(value || '')}
                    theme="vs-light"
                    options={{
                        minimap: { enabled: false },
                        fontSize: 14,
                        lineNumbers: 'on',
                        scrollBeyondLastLine: false,
                        wordWrap: 'on',
                        automaticLayout: true,
                    }}
                />
            </div>

            {error && (
                <div className="mt-2 p-3 bg-red-50 border border-red-200 rounded-md flex items-start gap-2">
                    <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                    <div className="flex-1">
                        <p className="text-sm font-medium text-red-800">Schema Error</p>
                        <p className="text-sm text-red-700 mt-1">{error}</p>
                    </div>
                </div>
            )}

            {isValid && !error && (
                <div className="mt-2 p-3 bg-green-50 border border-green-200 rounded-md flex items-center gap-2">
                    <CheckCircle2 className="w-5 h-5 text-green-600" />
                    <p className="text-sm font-medium text-green-800">Schema is valid</p>
                </div>
            )}
        </div>
    );
};
