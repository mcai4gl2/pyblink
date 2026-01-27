// Binary Viewer Component - Hex dump and decoded view for binary formats

import { Check, Copy, Download, Search, X } from 'lucide-react';
import React, { useState } from 'react';
import type { BinaryOutput } from '../types';
import { ByteSelectionPanel, type ByteSelection } from './ByteSelectionPanel';

interface BinaryViewerProps {
    title: string;
    output: BinaryOutput;
    format: 'compact' | 'native';
}

export const BinaryViewer: React.FC<BinaryViewerProps> = ({ title, output, format }) => {
    const [activeTab, setActiveTab] = useState<'hex' | 'decoded'>('hex');
    const [copiedHex, setCopiedHex] = useState(false);
    const [hoveredField, setHoveredField] = useState<string | null>(null);
    const [selection, setSelection] = useState<ByteSelection | null>(null);
    const [searchQuery, setSearchQuery] = useState('');
    const [showSearch, setShowSearch] = useState(false);

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
                        onClick={() => setShowSearch(!showSearch)}
                        className={`px-3 py-1 text-sm flex items-center gap-1.5 rounded transition-colors ${showSearch
                            ? 'bg-blue-100 text-blue-700 hover:bg-blue-200'
                            : 'text-gray-700 hover:text-gray-900 hover:bg-gray-100'
                            }`}
                        title="Search hex bytes"
                    >
                        <Search className="w-4 h-4" />
                        Search
                    </button>
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

            {/* Search Bar */}
            {showSearch && activeTab === 'hex' && (
                <div className="bg-blue-50 border-b border-blue-200 p-3">
                    <div className="flex items-center gap-2">
                        <Search className="w-4 h-4 text-gray-500" />
                        <input
                            type="text"
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value.toUpperCase())}
                            placeholder="Search hex bytes (e.g., 54 65 63 68 or 5465)"
                            className="flex-1 px-3 py-1.5 text-sm border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                        <button
                            onClick={() => {
                                setSearchQuery('');
                                setShowSearch(false);
                            }}
                            className="p-1.5 text-gray-500 hover:text-gray-700 hover:bg-gray-200 rounded transition-colors"
                            title="Close search"
                        >
                            <X className="w-4 h-4" />
                        </button>
                    </div>
                    {searchQuery && (
                        <p className="text-xs text-gray-600 mt-2">
                            Searching for: <code className="bg-white px-2 py-0.5 rounded">{searchQuery}</code>
                        </p>
                    )}
                </div>
            )}

            {/* Content */}
            <div className="bg-white">
                {activeTab === 'hex' ? (
                    <HexView
                        hex={output.hex}
                        hoveredField={hoveredField}
                        selection={selection}
                        onSelectionChange={setSelection}
                        searchQuery={searchQuery}
                    />
                ) : (
                    <DecodedView
                        decoded={output.decoded}
                        format={format}
                        onFieldHover={setHoveredField}
                    />
                )}
            </div>

            {/* Byte Selection Panel */}
            {activeTab === 'hex' && <ByteSelectionPanel selection={selection} />}
        </div>
    );
};

// Hex View Component
interface HexViewProps {
    hex: string;
    hoveredField: string | null;
    selection: ByteSelection | null;
    onSelectionChange: (selection: ByteSelection | null) => void;
    searchQuery: string;
}

const HexView: React.FC<HexViewProps> = ({ hex, selection, onSelectionChange, searchQuery }) => {
    const [hoveredByte, setHoveredByte] = useState<{ offset: number; byte: string } | null>(null);
    const [isDragging, setIsDragging] = useState(false);
    const [dragStart, setDragStart] = useState<number | null>(null);

    const lines = hex.split('\n');

    // Parse all bytes with their absolute offsets
    const allBytes: Array<{ offset: number; byte: string; lineIdx: number; byteIdx: number }> = [];
    lines.forEach((line, lineIdx) => {
        const [offsetStr, ...hexBytes] = line.split(/\s+/);
        const baseOffset = parseInt(offsetStr.replace(':', ''), 16);
        hexBytes.forEach((byte, byteIdx) => {
            if (byte) {
                allBytes.push({
                    offset: baseOffset + byteIdx,
                    byte: byte.toUpperCase(),
                    lineIdx,
                    byteIdx
                });
            }
        });
    });

    // Handle byte click
    const handleByteClick = (offset: number, byte: string) => {
        if (isDragging) return;

        // Single byte selection
        onSelectionChange({
            startOffset: offset,
            endOffset: offset,
            bytes: [byte]
        });
    };

    // Handle drag start
    const handleMouseDown = (offset: number) => {
        setIsDragging(true);
        setDragStart(offset);
    };

    // Handle drag over
    const handleMouseEnter = (offset: number, byte: string) => {
        setHoveredByte({ offset, byte });

        if (isDragging && dragStart !== null) {
            const start = Math.min(dragStart, offset);
            const end = Math.max(dragStart, offset);
            const selectedBytes = allBytes
                .filter(b => b.offset >= start && b.offset <= end)
                .map(b => b.byte);

            onSelectionChange({
                startOffset: start,
                endOffset: end,
                bytes: selectedBytes
            });
        }
    };

    // Handle drag end
    const handleMouseUp = () => {
        setIsDragging(false);
        setDragStart(null);
    };

    // Check if byte matches search query
    const matchesSearch = (byte: string, offset: number): boolean => {
        if (!searchQuery) return false;
        const cleanQuery = searchQuery.replace(/\s+/g, '');

        // Check if this byte starts a match
        const bytesFromHere = allBytes
            .filter(b => b.offset >= offset)
            .slice(0, cleanQuery.length / 2)
            .map(b => b.byte)
            .join('');

        return bytesFromHere.startsWith(cleanQuery);
    };

    // Check if byte is selected
    const isSelected = (offset: number): boolean => {
        if (!selection) return false;
        return offset >= selection.startOffset && offset <= selection.endOffset;
    };

    return (
        <div
            className="p-4 font-mono text-sm overflow-x-auto select-none"
            onMouseUp={handleMouseUp}
            onMouseLeave={() => {
                setHoveredByte(null);
                handleMouseUp();
            }}
        >
            <div className="space-y-1">
                {lines.map((line, lineIdx) => {
                    const [offsetStr, ...hexBytes] = line.split(/\s+/);
                    const baseOffset = parseInt(offsetStr.replace(':', ''), 16);

                    // Generate ASCII preview
                    const ascii = hexBytes
                        .map(byte => {
                            const code = parseInt(byte, 16);
                            return code >= 32 && code <= 126 ? String.fromCharCode(code) : '.';
                        })
                        .join('');

                    return (
                        <div key={lineIdx} className="flex gap-4 px-2 py-0.5 rounded hover:bg-gray-50">
                            {/* Offset */}
                            <span className="text-gray-500 select-none w-12">{offsetStr}</span>

                            {/* Hex Bytes */}
                            <div className="flex-1 flex flex-wrap gap-1">
                                {hexBytes.map((byte, byteIdx) => {
                                    if (!byte) return null;
                                    const offset = baseOffset + byteIdx;
                                    const selected = isSelected(offset);
                                    const searched = matchesSearch(byte, offset);
                                    const hovered = hoveredByte?.offset === offset;

                                    // Add visual separator every 4 bytes
                                    const separator = byteIdx > 0 && byteIdx % 4 === 0 ? (
                                        <span key={`sep-${byteIdx}`} className="text-gray-300 select-none">│</span>
                                    ) : null;

                                    return (
                                        <React.Fragment key={byteIdx}>
                                            {separator}
                                            <span
                                                className={`
                                                    px-1 py-0.5 rounded cursor-pointer transition-all relative
                                                    ${selected ? 'bg-orange-200 border border-orange-500 font-bold text-orange-900' : ''}
                                                    ${searched ? 'bg-yellow-200 border border-yellow-500 text-yellow-900' : ''}
                                                    ${!selected && !searched ? 'text-blue-700 hover:bg-blue-100' : ''}
                                                    ${hovered && !selected ? 'ring-2 ring-blue-400' : ''}
                                                `}
                                                onClick={() => handleByteClick(offset, byte)}
                                                onMouseDown={() => handleMouseDown(offset)}
                                                onMouseEnter={() => handleMouseEnter(offset, byte)}
                                                title={`Offset: ${offset} | Hex: ${byte} | Dec: ${parseInt(byte, 16)} | ASCII: ${parseInt(byte, 16) >= 32 && parseInt(byte, 16) <= 126
                                                    ? String.fromCharCode(parseInt(byte, 16))
                                                    : '·'
                                                    }`}
                                            >
                                                {byte}
                                            </span>
                                        </React.Fragment>
                                    );
                                })}
                            </div>

                            {/* ASCII Preview */}
                            <span className="text-gray-400 w-20 text-xs font-normal">
                                {ascii}
                            </span>
                        </div>
                    );
                })}
            </div>

            {/* Hover Tooltip */}
            {hoveredByte && !isDragging && (
                <div className="fixed bottom-4 right-4 bg-gray-900 text-white text-xs rounded-lg shadow-lg p-3 z-50 pointer-events-none">
                    <div className="space-y-1">
                        <div><span className="text-gray-400">Offset:</span> <span className="font-mono">{hoveredByte.offset}</span></div>
                        <div><span className="text-gray-400">Hex:</span> <span className="font-mono">{hoveredByte.byte}</span></div>
                        <div><span className="text-gray-400">Dec:</span> <span className="font-mono">{parseInt(hoveredByte.byte, 16)}</span></div>
                        <div><span className="text-gray-400">Bin:</span> <span className="font-mono">{parseInt(hoveredByte.byte, 16).toString(2).padStart(8, '0')}</span></div>
                        <div>
                            <span className="text-gray-400">ASCII:</span>{' '}
                            <span className="font-mono">
                                {parseInt(hoveredByte.byte, 16) >= 32 && parseInt(hoveredByte.byte, 16) <= 126
                                    ? String.fromCharCode(parseInt(hoveredByte.byte, 16))
                                    : '(non-printable)'}
                            </span>
                        </div>
                    </div>
                </div>
            )}
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
