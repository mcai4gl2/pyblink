// Input Panel Component with format selector and editor

import Editor from '@monaco-editor/react';
import { ArrowRight } from 'lucide-react';
import React from 'react';
import type { InputFormat } from '../types';

interface InputPanelProps {
    format: InputFormat;
    value: string;
    onChange: (value: string) => void;
    onFormatChange: (format: InputFormat) => void;
    onConvert: () => void;
    isLoading?: boolean;
}

const FORMAT_OPTIONS: { value: InputFormat; label: string }[] = [
    { value: 'tag', label: 'Tag Format' },
    { value: 'json', label: 'JSON Format' },
    { value: 'xml', label: 'XML Format' },
    { value: 'compact', label: 'Compact Binary (Hex)' },
    { value: 'native', label: 'Native Binary (Hex)' },
];

export const InputPanel: React.FC<InputPanelProps> = ({
    format,
    value,
    onChange,
    onFormatChange,
    onConvert,
    isLoading,
}) => {
    const getEditorLanguage = () => {
        switch (format) {
            case 'json':
                return 'json';
            case 'xml':
                return 'xml';
            default:
                return 'plaintext';
        }
    };

    return (
        <div className="flex flex-col h-full">
            <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-3">
                    <h2 className="text-lg font-semibold text-gray-800">Input Message</h2>
                    <select
                        value={format}
                        onChange={(e) => onFormatChange(e.target.value as InputFormat)}
                        className="px-3 py-1.5 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                        {FORMAT_OPTIONS.map((option) => (
                            <option key={option.value} value={option.value}>
                                {option.label}
                            </option>
                        ))}
                    </select>
                </div>
                <button
                    onClick={onConvert}
                    disabled={isLoading}
                    className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors text-sm font-medium flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    {isLoading ? (
                        <>
                            <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                            Converting...
                        </>
                    ) : (
                        <>
                            Convert
                            <ArrowRight className="w-4 h-4" />
                        </>
                    )}
                </button>
            </div>

            <div className="flex-1 border border-gray-300 rounded-md overflow-hidden">
                <Editor
                    height="100%"
                    language={getEditorLanguage()}
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
        </div>
    );
};
