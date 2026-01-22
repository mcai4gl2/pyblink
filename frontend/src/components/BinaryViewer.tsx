// Binary Viewer Component - Hex dump and decoded view for binary formats

import { Check, Copy, Download } from 'lucide-react';
import React, { useState } from 'react';
import type { BinaryOutput } from '../types';

interface BinaryViewerProps {
    title: string;
    output: BinaryOutput;
    format: 'compact' | 'native';
}

export const BinaryViewer: React.FC<BinaryViewerProps> = ({ title, output, format }) => {
    const [activeTab, setActiveTab] = useState<'hex' | 'decoded'>('hex');
    const [copiedHex, setCopiedHex] = useState(false);
    const [hoveredField, setHoveredField] = useState<string | null>(null);

    const copyHex = async () => {
        try {
            // Copy just the hex bytes without offsets
            const hexOnly = output.hex
                .split('\n')
                .map(line => line.substring(6)) // Remove "0000: " prefix
                .join(' ');
            await navigator.clipboard.writeText(hexOnly);
            setCopiedHex(true);
            setTimeout(() => setCopiedHex(false), 2000);
        } catch (err) {
            console.error('Failed to copy:', err);
        }
    };

    const downloadBinary = () => {
        try {
            // Convert hex string to bytes
            const hexOnly = output.hex
                .split('\n')
                .map(line => line.substring(6))
                .join(' ')
                .replace(/\s+/g, '');

            const bytes = new Uint8Array(
                hexOnly.match(/.{1,2}/g)?.map(byte => parseInt(byte, 16)) || []
            );

            const blob = new Blob([bytes], { type: 'application/octet-stream' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `message_${format}.bin`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        } catch (err) {
            console.error('Failed to download:', err);
        }
    };

    return (
        <div className="border border-gray-300 rounded-md overflow-hidden">
            {/* Header */}
            <div className="flex items-center justify-between p-3 bg-gray-50 border-b border-gray-300">
                <h3 className="font-medium text-gray-800">{title}</h3>
                <div className="flex items-center gap-2">
                    <button
                        onClick={copyHex}
                        className="px-3 py-1 text-sm text-gray-700 hover:text-gray-900 flex items-center gap-1.5 hover:bg-gray-100 rounded transition-colors"
                        title="Copy hex bytes"
                    >
                        {copiedHex ? (
                            <>
                                <Check className="w-4 h-4 text-green-600" />
                                Copied!
                            </>
                        ) : (
                            <>
                                <Copy className="w-4 h-4" />
                                Copy
                            </>
                        )}
                    </button>
                    <button
                        onClick={downloadBinary}
                        className="px-3 py-1 text-sm text-gray-700 hover:text-gray-900 flex items-center gap-1.5 hover:bg-gray-100 rounded transition-colors"
                        title="Download as .bin file"
                    >
                        <Download className="w-4 h-4" />
                        Download
                    </button>
                </div>
            </div>

            {/* Tab Navigation */}
            <div className="flex border-b border-gray-300 bg-white">
                <button
                    onClick={() => setActiveTab('hex')}
                    className={`px-4 py-2 text-sm font-medium transition-colors ${activeTab === 'hex'
                            ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50'
                            : 'text-gray-600 hover:text-gray-800 hover:bg-gray-50'
                        }`}
                >
                    Hex View
                </button>
                <button
                    onClick={() => setActiveTab('decoded')}
                    className={`px-4 py-2 text-sm font-medium transition-colors ${activeTab === 'decoded'
                            ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50'
                            : 'text-gray-600 hover:text-gray-800 hover:bg-gray-50'
                        }`}
                >
                    Decoded View
                </button>
            </div>

            {/* Content */}
            <div className="bg-white">
                {activeTab === 'hex' ? (
                    <HexView hex={output.hex} hoveredField={hoveredField} />
                ) : (
                    <DecodedView
                        decoded={output.decoded}
                        format={format}
                        onFieldHover={setHoveredField}
                    />
                )}
            </div>
        </div>
    );
};

// Hex View Component
interface HexViewProps {
    hex: string;
    hoveredField: string | null;
}

const HexView: React.FC<HexViewProps> = ({ hex }) => {
    const lines = hex.split('\n');

    return (
        <div className="p-4 font-mono text-sm overflow-x-auto">
            <div className="space-y-1">
                {lines.map((line, idx) => {
                    const [offset, ...hexBytes] = line.split(/\s+/);
                    const bytesStr = hexBytes.join(' ');

                    // Generate ASCII preview
                    const ascii = hexBytes
                        .map(byte => {
                            const code = parseInt(byte, 16);
                            return code >= 32 && code <= 126 ? String.fromCharCode(code) : '.';
                        })
                        .join('');

                    return (
                        <div key={idx} className="flex gap-4 hover:bg-gray-50 px-2 py-0.5 rounded">
                            <span className="text-gray-500 select-none w-12">{offset}</span>
                            <span className="text-blue-700 flex-1 font-semibold tracking-wider">
                                {bytesStr}
                            </span>
                            <span className="text-gray-400 w-16 text-xs">
                                {ascii}
                            </span>
                        </div>
                    );
                })}
            </div>
        </div>
    );
};

// Decoded View Component
interface DecodedViewProps {
    decoded: any;
    format: 'compact' | 'native';
    onFieldHover: (field: string | null) => void;
}

const DecodedView: React.FC<DecodedViewProps> = ({ decoded, format, onFieldHover }) => {
    return (
        <div className="p-4 space-y-4">
            {/* Header Information */}
            <div className="bg-gray-50 rounded-md p-3 space-y-2">
                <h4 className="text-sm font-semibold text-gray-700 mb-2">Message Header</h4>
                <div className="grid grid-cols-2 gap-2 text-sm">
                    <div>
                        <span className="text-gray-600">Size:</span>
                        <span className="ml-2 font-mono text-gray-900">{decoded.size} bytes</span>
                    </div>
                    <div>
                        <span className="text-gray-600">Type ID:</span>
                        <span className="ml-2 font-mono text-gray-900">{decoded.type_id}</span>
                    </div>
                    {format === 'native' && decoded.ext_offset !== undefined && (
                        <div>
                            <span className="text-gray-600">Extension Offset:</span>
                            <span className="ml-2 font-mono text-gray-900">{decoded.ext_offset}</span>
                        </div>
                    )}
                    <div>
                        <span className="text-gray-600">Fields:</span>
                        <span className="ml-2 font-mono text-gray-900">{decoded.fields.length}</span>
                    </div>
                </div>
            </div>

            {/* Fields */}
            <div>
                <h4 className="text-sm font-semibold text-gray-700 mb-2">Field Breakdown</h4>
                <div className="space-y-2">
                    {decoded.fields.map((field: any, idx: number) => (
                        <FieldRow
                            key={idx}
                            field={field}
                            index={idx}
                            onHover={onFieldHover}
                        />
                    ))}
                </div>
            </div>
        </div>
    );
};

// Field Row Component
interface FieldRowProps {
    field: any;
    index: number;
    onHover: (field: string | null) => void;
}

const FieldRow: React.FC<FieldRowProps> = ({ field, index, onHover }) => {
    const [isExpanded, setIsExpanded] = useState(false);

    return (
        <div
            className="border border-gray-200 rounded-md overflow-hidden hover:border-blue-300 transition-colors"
            onMouseEnter={() => onHover(field.name)}
            onMouseLeave={() => onHover(null)}
        >
            <div
                className="flex items-center justify-between p-2 bg-white cursor-pointer hover:bg-gray-50"
                onClick={() => setIsExpanded(!isExpanded)}
            >
                <div className="flex items-center gap-3 flex-1">
                    <span className="text-xs font-mono text-gray-500 w-6">#{index}</span>
                    <span className="font-medium text-gray-800">{field.name}</span>
                    <span className="text-sm text-gray-600 font-mono">{field.value}</span>
                </div>
                {field.offset !== undefined && (
                    <span className="text-xs text-gray-500 font-mono">
                        @{field.offset}
                    </span>
                )}
            </div>

            {isExpanded && field.bytes && (
                <div className="px-2 pb-2 bg-gray-50 border-t border-gray-200">
                    <div className="text-xs text-gray-600 mt-1">
                        <span className="font-medium">Bytes:</span>
                        <span className="ml-2 font-mono text-blue-700">{field.bytes}</span>
                    </div>
                </div>
            )}
        </div>
    );
};
