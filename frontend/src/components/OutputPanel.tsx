// Output Panel Component to display converted formats

import { Check, ChevronDown, ChevronRight, Copy } from 'lucide-react';
import React, { useState } from 'react';
import type { ConvertResponse } from '../types';

interface OutputPanelProps {
    result: ConvertResponse | null;
}

export const OutputPanel: React.FC<OutputPanelProps> = ({ result }) => {
    const [copiedFormat, setCopiedFormat] = useState<string | null>(null);
    const [expandedSections, setExpandedSections] = useState<Set<string>>(
        new Set(['tag', 'json', 'xml', 'compact_binary', 'native_binary'])
    );

    const copyToClipboard = async (text: string, format: string) => {
        try {
            await navigator.clipboard.writeText(text);
            setCopiedFormat(format);
            setTimeout(() => setCopiedFormat(null), 2000);
        } catch (err) {
            console.error('Failed to copy:', err);
        }
    };

    const toggleSection = (section: string) => {
        const newExpanded = new Set(expandedSections);
        if (newExpanded.has(section)) {
            newExpanded.delete(section);
        } else {
            newExpanded.add(section);
        }
        setExpandedSections(newExpanded);
    };

    if (!result) {
        return (
            <div className="flex items-center justify-center h-full text-gray-500">
                <p>Enter a schema and message, then click Convert to see outputs</p>
            </div>
        );
    }

    if (!result.success) {
        return (
            <div className="p-4">
                <div className="p-4 bg-red-50 border border-red-200 rounded-md">
                    <p className="text-sm font-medium text-red-800">Conversion Error</p>
                    <p className="text-sm text-red-700 mt-1">{result.error}</p>
                </div>
            </div>
        );
    }

    const outputs = result.outputs!;

    return (
        <div className="flex flex-col h-full overflow-auto">
            <div className="p-4 space-y-3">
                {/* Tag Format */}
                {outputs.tag && (
                    <OutputSection
                        title="Tag Format"
                        content={outputs.tag}
                        format="tag"
                        isExpanded={expandedSections.has('tag')}
                        onToggle={() => toggleSection('tag')}
                        onCopy={() => copyToClipboard(outputs.tag!, 'tag')}
                        isCopied={copiedFormat === 'tag'}
                    />
                )}

                {/* JSON Format */}
                {outputs.json && (
                    <OutputSection
                        title="JSON Format"
                        content={outputs.json}
                        format="json"
                        language="json"
                        isExpanded={expandedSections.has('json')}
                        onToggle={() => toggleSection('json')}
                        onCopy={() => copyToClipboard(outputs.json!, 'json')}
                        isCopied={copiedFormat === 'json'}
                    />
                )}

                {/* XML Format */}
                {outputs.xml && (
                    <OutputSection
                        title="XML Format"
                        content={outputs.xml}
                        format="xml"
                        language="xml"
                        isExpanded={expandedSections.has('xml')}
                        onToggle={() => toggleSection('xml')}
                        onCopy={() => copyToClipboard(outputs.xml!, 'xml')}
                        isCopied={copiedFormat === 'xml'}
                    />
                )}

                {/* Compact Binary */}
                {outputs.compact_binary && (
                    <BinaryOutputSection
                        title="Compact Binary"
                        output={outputs.compact_binary}
                        format="compact_binary"
                        isExpanded={expandedSections.has('compact_binary')}
                        onToggle={() => toggleSection('compact_binary')}
                        onCopy={() => copyToClipboard(outputs.compact_binary!.hex, 'compact_binary')}
                        isCopied={copiedFormat === 'compact_binary'}
                    />
                )}

                {/* Native Binary */}
                {outputs.native_binary && (
                    <BinaryOutputSection
                        title="Native Binary"
                        output={outputs.native_binary}
                        format="native_binary"
                        isExpanded={expandedSections.has('native_binary')}
                        onToggle={() => toggleSection('native_binary')}
                        onCopy={() => copyToClipboard(outputs.native_binary!.hex, 'native_binary')}
                        isCopied={copiedFormat === 'native_binary'}
                    />
                )}
            </div>
        </div>
    );
};

// Output Section Component
interface OutputSectionProps {
    title: string;
    content: string;
    format: string;
    language?: string;
    isExpanded: boolean;
    onToggle: () => void;
    onCopy: () => void;
    isCopied: boolean;
}

const OutputSection: React.FC<OutputSectionProps> = ({
    title,
    content,
    isExpanded,
    onToggle,
    onCopy,
    isCopied,
}) => {
    return (
        <div className="border border-gray-300 rounded-md overflow-hidden">
            <div
                className="flex items-center justify-between p-3 bg-gray-50 cursor-pointer hover:bg-gray-100 transition-colors"
                onClick={onToggle}
            >
                <div className="flex items-center gap-2">
                    {isExpanded ? (
                        <ChevronDown className="w-4 h-4 text-gray-600" />
                    ) : (
                        <ChevronRight className="w-4 h-4 text-gray-600" />
                    )}
                    <h3 className="font-medium text-gray-800">{title}</h3>
                </div>
                <button
                    onClick={(e) => {
                        e.stopPropagation();
                        onCopy();
                    }}
                    className="px-3 py-1 text-sm text-gray-700 hover:text-gray-900 flex items-center gap-1.5"
                >
                    {isCopied ? (
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
            </div>
            {isExpanded && (
                <div className="p-3 bg-white">
                    <pre className="text-sm font-mono whitespace-pre-wrap break-all">
                        {content}
                    </pre>
                </div>
            )}
        </div>
    );
};

// Binary Output Section Component
interface BinaryOutputSectionProps {
    title: string;
    output: { hex: string; decoded: any };
    format: string;
    isExpanded: boolean;
    onToggle: () => void;
    onCopy: () => void;
    isCopied: boolean;
}

const BinaryOutputSection: React.FC<BinaryOutputSectionProps> = ({
    title,
    output,
    isExpanded,
    onToggle,
    onCopy,
    isCopied,
}) => {
    return (
        <div className="border border-gray-300 rounded-md overflow-hidden">
            <div
                className="flex items-center justify-between p-3 bg-gray-50 cursor-pointer hover:bg-gray-100 transition-colors"
                onClick={onToggle}
            >
                <div className="flex items-center gap-2">
                    {isExpanded ? (
                        <ChevronDown className="w-4 h-4 text-gray-600" />
                    ) : (
                        <ChevronRight className="w-4 h-4 text-gray-600" />
                    )}
                    <h3 className="font-medium text-gray-800">{title}</h3>
                </div>
                <button
                    onClick={(e) => {
                        e.stopPropagation();
                        onCopy();
                    }}
                    className="px-3 py-1 text-sm text-gray-700 hover:text-gray-900 flex items-center gap-1.5"
                >
                    {isCopied ? (
                        <>
                            <Check className="w-4 h-4 text-green-600" />
                            Copied!
                        </>
                    ) : (
                        <>
                            <Copy className="w-4 h-4" />
                            Copy Hex
                        </>
                    )}
                </button>
            </div>
            {isExpanded && (
                <div className="p-3 bg-white space-y-3">
                    <div>
                        <p className="text-xs font-medium text-gray-600 mb-1">Hex View:</p>
                        <pre className="text-sm font-mono whitespace-pre-wrap break-all bg-gray-50 p-2 rounded">
                            {output.hex}
                        </pre>
                    </div>
                    <div>
                        <p className="text-xs font-medium text-gray-600 mb-1">Decoded:</p>
                        <div className="text-sm space-y-1">
                            <p>
                                <span className="font-medium">Size:</span> {output.decoded.size} bytes
                            </p>
                            <p>
                                <span className="font-medium">Type ID:</span> {output.decoded.type_id}
                            </p>
                            {output.decoded.ext_offset !== undefined && (
                                <p>
                                    <span className="font-medium">Extension Offset:</span>{' '}
                                    {output.decoded.ext_offset}
                                </p>
                            )}
                            <p>
                                <span className="font-medium">Fields:</span> {output.decoded.fields.length}
                            </p>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};
