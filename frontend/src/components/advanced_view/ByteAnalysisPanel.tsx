import { Copy, Info } from 'lucide-react';
import React, { useMemo, useState } from 'react';
import { BinarySection } from '../../types';

interface ByteAnalysisPanelProps {
    section?: BinarySection;
    hexData: string; // The full hex string of the message
}

export const ByteAnalysisPanel: React.FC<ByteAnalysisPanelProps> = ({ section, hexData }) => {
    const [endianness, setEndianness] = useState<'little' | 'big'>('little');

    // Extract bytes for the selected section
    const bytes = useMemo(() => {
        if (!section || !hexData) return null;
        // section offsets are 0-based byte indices
        // hexData is hex string (2 chars per byte)
        const start = section.startOffset * 2;
        const end = section.endOffset * 2;

        if (start >= hexData.length) return null;

        const hexSegment = hexData.slice(start, end);
        const byteArray = new Uint8Array(hexSegment.length / 2);
        for (let i = 0; i < byteArray.length; i++) {
            byteArray[i] = parseInt(hexSegment.slice(i * 2, i * 2 + 2), 16);
        }
        return byteArray;
    }, [section, hexData]);

    if (!section || !bytes) {
        return (
            <div className="h-full flex flex-col justify-center items-center text-gray-400 italic bg-gray-50">
                <Info className="w-8 h-8 mb-2 opacity-50" />
                Select a field or byte range to see detailed analysis
            </div>
        );
    }

    const copyToClipboard = (text: string) => {
        navigator.clipboard.writeText(text);
        // Could add toast here
    };

    // Helper functions for formatting
    const getHexRep = () => {
        return Array.from(bytes).map(b => b.toString(16).padStart(2, '0').toUpperCase()).join(' ');
    };

    type Endianness = 'little' | 'big';

    const getDecimalRep = (endian: Endianness) => {
        // Interpret as integer based on length
        // If length > 8, show as byte array or arbitrary precision int?
        // JS max safe integer is 2^53.
        // For standard sizes 1, 2, 4, 8:
        if (bytes.length > 8) return "Too large for int view";

        let val = BigInt(0);
        if (endian === 'little') {
            for (let i = 0; i < bytes.length; i++) {
                val += BigInt(bytes[i]) << BigInt(i * 8);
            }
        } else {
            for (let i = 0; i < bytes.length; i++) {
                val = (val << BigInt(8)) + BigInt(bytes[i]);
            }
        }

        // Handle signed interpretation?
        // Assuming unsigned for Generic view, unless type hint available.
        // Analyzer gives 'dataType' e.g. "i32".

        return val.toString();
    };

    const getBinaryRep = () => {
        // Show up to 8 bytes in binary?
        if (bytes.length > 8) return "Too large for binary view";
        return Array.from(bytes).map(b => b.toString(2).padStart(8, '0')).join(' ');
    };

    const getAsciiRep = () => {
        // Replace non-printable with .
        return Array.from(bytes).map(b => (b >= 32 && b <= 126) ? String.fromCharCode(b) : '.').join('');
    };

    return (
        <div className="h-full flex flex-col bg-gray-50">
            {/* Header */}
            <div className="px-4 py-2 border-b border-gray-200 flex items-center justify-between bg-white">
                <div className="flex items-center gap-2">
                    <Info className="w-4 h-4 text-blue-600" />
                    <span className="text-sm font-medium text-gray-700">Byte Analysis</span>
                    <span className="text-xs text-gray-400 border-l border-gray-300 pl-2 ml-2">
                        {section.endOffset - section.startOffset} bytes @ {section.startOffset}
                    </span>
                </div>

                {/* Endianness Toggle (only relevant for multi-byte numerics) */}
                {bytes.length > 1 && (
                    <div className="flex bg-gray-100 rounded p-0.5 text-xs">
                        <button
                            onClick={() => setEndianness('little')}
                            className={`px-2 py-0.5 rounded ${endianness === 'little' ? 'bg-white shadow text-gray-800 font-medium' : 'text-gray-500 hover:text-gray-700'}`}
                        >
                            Little Endian
                        </button>
                        <button
                            onClick={() => setEndianness('big')}
                            className={`px-2 py-0.5 rounded ${endianness === 'big' ? 'bg-white shadow text-gray-800 font-medium' : 'text-gray-500 hover:text-gray-700'}`}
                        >
                            Big Endian
                        </button>
                    </div>
                )}
            </div>

            <div className="flex-1 p-4 overflow-y-auto">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">

                    {/* 1. Analyzed Value (from Backend) */}
                    <div className="bg-white border border-gray-200 rounded p-3 relative group">
                        <div className="text-xs text-gray-500 mb-1 uppercase tracking-wider">Interpreted ({section.dataType})</div>
                        <div className="font-mono text-gray-900 text-lg font-medium truncate" title={section.interpretedValue}>{section.interpretedValue}</div>
                        <button onClick={() => copyToClipboard(section.interpretedValue || '')} className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 p-1 hover:bg-gray-100 rounded text-gray-400">
                            <Copy className="w-3 h-3" />
                        </button>
                    </div>

                    {/* 2. Hex Representation */}
                    <div className="bg-white border border-gray-200 rounded p-3 relative group">
                        <div className="text-xs text-gray-500 mb-1 uppercase tracking-wider">Hexadecimal</div>
                        <div className="font-mono text-gray-900 break-all text-sm">{getHexRep()}</div>
                        <button onClick={() => copyToClipboard(getHexRep().replace(/ /g, ''))} className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 p-1 hover:bg-gray-100 rounded text-gray-400">
                            <Copy className="w-3 h-3" />
                        </button>
                    </div>

                    {/* 3. Decimal Representation (Calculated) */}
                    <div className="bg-white border border-gray-200 rounded p-3 relative group">
                        <div className="text-xs text-gray-500 mb-1 uppercase tracking-wider">
                            Decimal ({endianness === 'little' ? 'LE' : 'BE'})
                        </div>
                        <div className="font-mono text-gray-900 text-sm truncate">
                            {getDecimalRep(endianness)}
                        </div>
                        <button onClick={() => copyToClipboard(getDecimalRep(endianness))} className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 p-1 hover:bg-gray-100 rounded text-gray-400">
                            <Copy className="w-3 h-3" />
                        </button>
                    </div>

                    {/* 4. ASCII Preview */}
                    <div className="bg-white border border-gray-200 rounded p-3 relative group">
                        <div className="text-xs text-gray-500 mb-1 uppercase tracking-wider">ASCII</div>
                        <div className="font-mono text-gray-900 text-sm tracking-widest">{getAsciiRep()}</div>
                    </div>

                    {/* 5. Binary (if small) */}
                    {bytes.length <= 8 && (
                        <div className="bg-white border border-gray-200 rounded p-3 relative group col-span-2">
                            <div className="text-xs text-gray-500 mb-1 uppercase tracking-wider">Binary</div>
                            <div className="font-mono text-gray-900 text-xs tracking-wider break-all">
                                {getBinaryRep()}
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};
