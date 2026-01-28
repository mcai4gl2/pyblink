import { Copy, Info } from 'lucide-react';
import React from 'react';

export const ByteAnalysisPanel: React.FC = () => {
    return (
        <div className="h-full flex flex-col">
            <div className="px-4 py-2 border-b border-gray-200 flex items-center gap-2">
                <Info className="w-4 h-4 text-blue-600" />
                <span className="text-sm font-medium text-gray-700">Byte Analysis</span>
            </div>

            <div className="flex-1 p-4 flex gap-8">
                {/* Selection Info */}
                <div className="flex flex-col gap-1 min-w-[200px]">
                    <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Selection</span>
                    <div className="text-sm text-gray-800">
                        <span className="font-mono bg-gray-100 px-1.5 py-0.5 rounded">Bytes 0-3</span>
                        <span className="text-gray-400 mx-2">•</span>
                        <span>4 bytes</span>
                    </div>
                    <div className="text-xs text-blue-600 mt-1">Message Size (Header)</div>
                </div>

                {/* Values */}
                <div className="flex-1 grid grid-cols-4 gap-6">
                    {/* Hex */}
                    <div className="bg-white border border-gray-200 rounded p-2 relative group">
                        <div className="text-xs text-gray-500 mb-1">Hex</div>
                        <div className="font-mono text-gray-900">70 00 00 00</div>
                        <button className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 p-1 hover:bg-gray-100 rounded text-gray-400 hover:text-blue-600 transition-all">
                            <Copy className="w-3 h-3" />
                        </button>
                    </div>

                    {/* Decimal */}
                    <div className="bg-white border border-gray-200 rounded p-2 relative group">
                        <div className="text-xs text-gray-500 mb-1">Decimal (Little Endian)</div>
                        <div className="font-mono text-gray-900">112</div>
                        <button className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 p-1 hover:bg-gray-100 rounded text-gray-400 hover:text-blue-600 transition-all">
                            <Copy className="w-3 h-3" />
                        </button>
                    </div>

                    {/* Binary */}
                    <div className="bg-white border border-gray-200 rounded p-2 relative group col-span-2">
                        <div className="text-xs text-gray-500 mb-1">Binary</div>
                        <div className="font-mono text-gray-900 text-xs mt-1">01110000 00000000 00000000 00000000</div>
                        <button className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 p-1 hover:bg-gray-100 rounded text-gray-400 hover:text-blue-600 transition-all">
                            <Copy className="w-3 h-3" />
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};
