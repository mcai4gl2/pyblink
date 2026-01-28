import { Layout, Maximize2, Minimize2, X } from 'lucide-react';
import React, { useEffect, useState } from 'react';
import { analyzeBinary } from '../../services/api';
import { BinarySection, MessageField } from '../../types';
import { BinaryHexPane } from './BinaryHexPane';
import { ByteAnalysisPanel } from './ByteAnalysisPanel';
import { MessageStructurePane } from './MessageStructurePane';

interface AdvancedBinaryViewProps {
    isOpen: boolean;
    onClose: () => void;
    schema: string;
    hexData: string;
}

export const AdvancedBinaryView: React.FC<AdvancedBinaryViewProps> = ({ isOpen, onClose, schema, hexData }) => {
    const [isMaximized, setIsMaximized] = useState(false);

    // Clean hex data (remove offsets, spaces, newlines)
    const cleanHexData = hexData ? hexData.replace(/[^0-9A-Fa-f]/g, '') : '';

    // Data State
    const [sections, setSections] = useState<BinarySection[]>([]);
    const [fields, setFields] = useState<MessageField[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [selectedSectionId, setSelectedSectionId] = useState<string | null>(null);

    // State for toggles
    const [structureFormat, setStructureFormat] = useState<'json' | 'tag'>('json');
    const [viewMode, setViewMode] = useState<'hex' | 'decimal' | 'binary'>('hex');

    // Fetch analysis when opened or data changes
    useEffect(() => {
        if (isOpen && schema && cleanHexData) {
            fetchAnalysis();
        } else {
            // Reset if closed or empty
            if (!isOpen) {
                setSections([]);
                setFields([]);
                setError(null);
                setSelectedSectionId(null);
            }
        }
    }, [isOpen, schema, cleanHexData]);

    const fetchAnalysis = async () => {
        setIsLoading(true);
        setError(null);
        try {
            const response = await analyzeBinary({ schema, binary_hex: cleanHexData });
            if (response.success) {
                setSections(response.sections);
                setFields(response.fields);
            } else {
                setError(response.error || "Analysis failed");
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to analyze binary");
        } finally {
            setIsLoading(false);
        }
    };

    if (!isOpen) return null;

    const toggleMaximize = () => setIsMaximized(!isMaximized);

    // Find selected section data
    const selectedSection = sections.find(s => s.id === selectedSectionId);

    return (
        <div className={`fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm transition-all duration-300 ${isOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'}`}>
            <div className={`bg-white rounded-lg shadow-2xl flex flex-col transition-all duration-300 ${isMaximized ? 'w-full h-full' : 'w-[90vw] h-[85vh] max-w-7xl'}`}>

                {/* Header */}
                <header className="flex items-center justify-between px-4 py-3 border-b border-gray-200 bg-gray-50 rounded-t-lg">
                    <div className="flex items-center gap-2">
                        <Layout className="w-5 h-5 text-blue-600" />
                        <h2 className="text-lg font-semibold text-gray-800">Advanced Binary Inspector</h2>
                        {isLoading && <span className="text-xs text-gray-500 animate-pulse ml-2">Analyzing...</span>}
                        {error && <span className="text-xs text-red-500 ml-2">Error: {error}</span>}
                    </div>
                    <div className="flex items-center gap-2">
                        <button
                            onClick={toggleMaximize}
                            className="p-1.5 text-gray-500 hover:text-gray-700 hover:bg-gray-200 rounded transition-colors"
                            title={isMaximized ? "Restore" : "Maximize"}
                        >
                            {isMaximized ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
                        </button>
                        <button
                            onClick={onClose}
                            className="p-1.5 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded transition-colors"
                            title="Close"
                        >
                            <X className="w-5 h-5" />
                        </button>
                    </div>
                </header>

                {/* Main Content (Split Pane) */}
                <div className="flex-1 flex overflow-hidden">
                    {/* Left Pane - Message Structure */}
                    <div className="w-1/2 border-r border-gray-200 flex flex-col min-w-[300px]">
                        <MessageStructurePane
                            format={structureFormat}
                            onFormatChange={setStructureFormat}
                            fields={fields}
                            onFieldSelect={(id) => setSelectedSectionId(id)}
                            selectedSectionId={selectedSectionId}
                        />
                    </div>

                    {/* Right Pane - Binary Hex View */}
                    <div className="w-1/2 flex flex-col min-w-[300px]">
                        <BinaryHexPane
                            viewMode={viewMode}
                            onViewModeChange={setViewMode}
                            hexData={cleanHexData}
                            sections={sections}
                            selectedSectionId={selectedSectionId}
                            onSectionSelect={setSelectedSectionId}
                        />
                    </div>
                </div>

                {/* Bottom Panel - Byte Analysis */}
                <div className="h-48 border-t border-gray-200 bg-gray-50 shrink-0">
                    <ByteAnalysisPanel section={selectedSection} hexData={cleanHexData} />
                </div>
            </div>
        </div>
    );
};
