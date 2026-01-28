import { Binary, Hash, Hexagon } from 'lucide-react';
import React from 'react';

interface BinaryHexPaneProps {
    viewMode: 'hex' | 'decimal' | 'binary';
    onViewModeChange: (mode: 'hex' | 'decimal' | 'binary') => void;
}

export const BinaryHexPane: React.FC<BinaryHexPaneProps> = ({ viewMode, onViewModeChange }) => {
    return (
        <div className="flex flex-col h-full bg-white">
            {/* Toolbar */}
            <div className="flex items-center justify-between px-3 py-2 border-b border-gray-200">
                <span className="text-sm font-medium text-gray-700">Binary Representation</span>
                <div className="flex bg-gray-100 rounded p-0.5">
                    <button
                        onClick={() => onViewModeChange('hex')}
                        className={`px-2 py-1 text-xs font-medium rounded flex items-center gap-1.5 transition-all
                            ${viewMode === 'hex' ? 'bg-white text-blue-600 shadow-sm' : 'text-gray-500 hover:text-gray-700'}`}
                        title="Hexadecimal View"
                    >
                        <Hexagon className="w-3.5 h-3.5" />
                        Hex
                    </button>
                    <button
                        onClick={() => onViewModeChange('decimal')}
                        className={`px-2 py-1 text-xs font-medium rounded flex items-center gap-1.5 transition-all
                            ${viewMode === 'decimal' ? 'bg-white text-blue-600 shadow-sm' : 'text-gray-500 hover:text-gray-700'}`}
                        title="Decimal View"
                    >
                        <Hash className="w-3.5 h-3.5" />
                        Dec
                    </button>
                    <button
                        onClick={() => onViewModeChange('binary')}
                        className={`px-2 py-1 text-xs font-medium rounded flex items-center gap-1.5 transition-all
                            ${viewMode === 'binary' ? 'bg-white text-blue-600 shadow-sm' : 'text-gray-500 hover:text-gray-700'}`}
                        title="Binary View"
                    >
                        <Binary className="w-3.5 h-3.5" />
                        Bin
                    </button>
                </div>
            </div>

            {/* Hex Grid Area */}
            <div className="flex-1 overflow-auto p-4 font-mono text-sm bg-gray-50/50">
                <div className="text-gray-400 italic mb-4">
                    {/* Placeholder for Hex Grid */}
                    Binary data grid will appear here...
                </div>

                {/* Simulated Hex View */}
                <div className="grid grid-cols-[auto_1fr] gap-4">
                    {/* Offsets */}
                    <div className="flex flex-col text-gray-400 select-none border-r border-gray-200 pr-3 text-right">
                        <div>0000:</div>
                        <div>0008:</div>
                        <div>0010:</div>
                    </div>

                    {/* Bytes */}
                    <div className="font-mono text-gray-800">
                        {/* Row 1 */}
                        <div className="flex gap-2 mb-1">
                            <span className="bg-blue-100 text-blue-900 px-0.5 rounded">70</span>
                            <span className="bg-blue-100 text-blue-900 px-0.5 rounded">00</span>
                            <span className="bg-blue-100 text-blue-900 px-0.5 rounded">00</span>
                            <span className="bg-blue-100 text-blue-900 px-0.5 rounded">00</span>
                            <span className="text-gray-300">|</span>
                            <span className="bg-blue-100 text-blue-900 px-0.5 rounded">04</span>
                            <span className="bg-blue-100 text-blue-900 px-0.5 rounded">00</span>
                            <span className="bg-blue-100 text-blue-900 px-0.5 rounded">00</span>
                            <span className="bg-blue-100 text-blue-900 px-0.5 rounded">00</span>
                        </div>
                        {/* Row 2 */}
                        <div className="flex gap-2 mb-1">
                            <span className="bg-blue-100 text-blue-900 px-0.5 rounded">00</span>
                            <span className="bg-blue-100 text-blue-900 px-0.5 rounded">00</span>
                            <span className="bg-blue-100 text-blue-900 px-0.5 rounded">00</span>
                            <span className="bg-blue-100 text-blue-900 px-0.5 rounded">00</span>
                            <span className="text-gray-300">|</span>
                            <span className="bg-green-100 text-green-900 px-0.5 rounded">54</span>
                            <span className="bg-green-100 text-green-900 px-0.5 rounded">65</span>
                            <span className="bg-green-100 text-green-900 px-0.5 rounded">63</span>
                            <span className="bg-green-100 text-green-900 px-0.5 rounded">68</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};
