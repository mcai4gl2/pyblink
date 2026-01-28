import { Layout, Maximize2, Minimize2, X } from 'lucide-react';
import React, { useState } from 'react';
import { BinaryHexPane } from './BinaryHexPane';
import { ByteAnalysisPanel } from './ByteAnalysisPanel';
import { MessageStructurePane } from './MessageStructurePane';

interface AdvancedBinaryViewProps {
    isOpen: boolean;
    onClose: () => void;
}

export const AdvancedBinaryView: React.FC<AdvancedBinaryViewProps> = ({ isOpen, onClose }) => {
    const [isMaximized, setIsMaximized] = useState(false);

    // State for toggles
    const [structureFormat, setStructureFormat] = useState<'json' | 'tag'>('json');
    const [viewMode, setViewMode] = useState<'hex' | 'decimal' | 'binary'>('hex');

    if (!isOpen) return null;

    const toggleMaximize = () => setIsMaximized(!isMaximized);

    return (
        <div className={`fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm transition-all duration-300 ${isOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'}`}>
            <div className={`bg-white rounded-lg shadow-2xl flex flex-col transition-all duration-300 ${isMaximized ? 'w-full h-full' : 'w-[90vw] h-[85vh] max-w-7xl'}`}>

                {/* Header */}
                <header className="flex items-center justify-between px-4 py-3 border-b border-gray-200 bg-gray-50 rounded-t-lg">
                    <div className="flex items-center gap-2">
                        <Layout className="w-5 h-5 text-blue-600" />
                        <h2 className="text-lg font-semibold text-gray-800">Advanced Binary Inspector</h2>
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
                        />
                    </div>

                    {/* Right Pane - Binary Hex View */}
                    <div className="w-1/2 flex flex-col min-w-[300px]">
                        <BinaryHexPane
                            viewMode={viewMode}
                            onViewModeChange={setViewMode}
                        />
                    </div>
                </div>

                {/* Bottom Panel - Byte Analysis */}
                <div className="h-48 border-t border-gray-200 bg-gray-50 shrink-0">
                    <ByteAnalysisPanel />
                </div>
            </div>
        </div>
    );
};
