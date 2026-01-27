// Byte Selection Panel - Shows details about selected bytes
import { Check, Copy } from 'lucide-react';
import React, { useState } from 'react';

export interface ByteSelection {
    startOffset: number;
    endOffset: number;
    bytes: string[];
}

interface ByteSelectionPanelProps {
    selection: ByteSelection | null;
}

export const ByteSelectionPanel: React.FC<ByteSelectionPanelProps> = ({ selection }) => {
    const [copiedHex, setCopiedHex] = useState(false);
    const [copiedAscii, setCopiedAscii] = useState(false);

    if (!selection) {
        return (
            <div className="border-t border-gray-300 bg-gray-50 p-4">
                <p className="text-sm text-gray-500 text-center">
                    Click on a byte or drag to select a range to see details
                </p>
            </div>
        );
    }

    const { startOffset, endOffset, bytes } = selection;
    const byteCount = bytes.length;

    // Convert bytes to different representations
    const hexString = bytes.join(' ');
    const decimalValues = bytes.map(b => parseInt(b, 16));
    const decimalString = decimalValues.join(' ');

    // Generate ASCII representation
    const asciiString = bytes
        .map(byte => {
            const code = parseInt(byte, 16);
            return code >= 32 && code <= 126 ? String.fromCharCode(code) : '.';
        })
        .join('');

    // Generate binary representation
    const binaryString = bytes
        .map(byte => parseInt(byte, 16).toString(2).padStart(8, '0'))
        .join(' ');

    const copyHex = async () => {
        try {
            await navigator.clipboard.writeText(hexString);
            setCopiedHex(true);
            setTimeout(() => setCopiedHex(false), 2000);
        } catch (err) {
            console.error('Failed to copy:', err);
        }
    };

    const copyAscii = async () => {
        try {
            await navigator.clipboard.writeText(asciiString);
            setCopiedAscii(true);
            setTimeout(() => setCopiedAscii(false), 2000);
        } catch (err) {
            console.error('Failed to copy:', err);
        }
    };

    return (
        <div className="border-t border-gray-300 bg-gradient-to-br from-blue-50 to-indigo-50 p-4">
            <div className="space-y-3">
                {/* Header */}
                <div className="flex items-center justify-between">
                    <h4 className="text-sm font-semibold text-gray-800">
                        Selection Info: Bytes {startOffset}-{endOffset} ({byteCount} byte{byteCount !== 1 ? 's' : ''})
                    </h4>
                    <div className="flex gap-2">
                        <button
                            onClick={copyHex}
                            className="px-2 py-1 text-xs text-gray-700 hover:text-gray-900 flex items-center gap-1 hover:bg-white/50 rounded transition-colors"
                            title="Copy hex values"
                        >
                            {copiedHex ? (
                                <>
                                    <Check className="w-3 h-3 text-green-600" />
                                    Copied!
                                </>
                            ) : (
                                <>
                                    <Copy className="w-3 h-3" />
                                    Copy Hex
                                </>
                            )}
                        </button>
                        <button
                            onClick={copyAscii}
                            className="px-2 py-1 text-xs text-gray-700 hover:text-gray-900 flex items-center gap-1 hover:bg-white/50 rounded transition-colors"
                            title="Copy ASCII representation"
                        >
                            {copiedAscii ? (
                                <>
                                    <Check className="w-3 h-3 text-green-600" />
                                    Copied!
                                </>
                            ) : (
                                <>
                                    <Copy className="w-3 h-3" />
                                    Copy ASCII
                                </>
                            )}
                        </button>
                    </div>
                </div>

                {/* Data representations */}
                <div className="grid grid-cols-1 gap-2 bg-white rounded-md p-3 shadow-sm">
                    <div className="flex flex-col gap-1">
                        <span className="text-xs font-medium text-gray-600">Hex:</span>
                        <code className="text-sm font-mono text-blue-700 break-all">{hexString}</code>
                    </div>

                    <div className="flex flex-col gap-1">
                        <span className="text-xs font-medium text-gray-600">Decimal:</span>
                        <code className="text-sm font-mono text-purple-700 break-all">{decimalString}</code>
                    </div>

                    <div className="flex flex-col gap-1">
                        <span className="text-xs font-medium text-gray-600">Binary:</span>
                        <code className="text-xs font-mono text-green-700 break-all">{binaryString}</code>
                    </div>

                    <div className="flex flex-col gap-1">
                        <span className="text-xs font-medium text-gray-600">ASCII:</span>
                        <code className="text-sm font-mono text-gray-800 break-all bg-gray-50 px-2 py-1 rounded">
                            {asciiString || '(non-printable)'}
                        </code>
                    </div>

                    {/* Additional interpretations for common sizes */}
                    {byteCount === 4 && (
                        <div className="flex flex-col gap-1 border-t border-gray-200 pt-2 mt-1">
                            <span className="text-xs font-medium text-gray-600">As u32 (little-endian):</span>
                            <code className="text-sm font-mono text-orange-700">
                                {decimalValues[0] + (decimalValues[1] << 8) + (decimalValues[2] << 16) + (decimalValues[3] << 24)}
                            </code>
                        </div>
                    )}

                    {byteCount === 2 && (
                        <div className="flex flex-col gap-1 border-t border-gray-200 pt-2 mt-1">
                            <span className="text-xs font-medium text-gray-600">As u16 (little-endian):</span>
                            <code className="text-sm font-mono text-orange-700">
                                {decimalValues[0] + (decimalValues[1] << 8)}
                            </code>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};
