import { Binary, Hash, Hexagon } from 'lucide-react';
import React from 'react';
import { BinarySection } from '../../types';

interface BinaryHexPaneProps {
    viewMode: 'hex' | 'decimal' | 'binary';
    onViewModeChange: (mode: 'hex' | 'decimal' | 'binary') => void;
    hexData?: string;
    sections?: BinarySection[];
    selectedSectionId?: string | null;
    onSectionSelect?: (sectionId: string | null) => void;
}

const COLOR_MAP: Record<string, string> = {
    blue: "bg-blue-100 text-blue-900 border-blue-200",
    green: "bg-green-100 text-green-900 border-green-200",
    yellow: "bg-amber-100 text-amber-900 border-amber-200",
    purple: "bg-purple-100 text-purple-900 border-purple-200",
    orange: "bg-orange-100 text-orange-900 border-orange-200",
    red: "bg-red-100 text-red-900 border-red-200",
    gray: "bg-gray-100 text-gray-600 border-gray-200",
    pink: "bg-pink-100 text-pink-900 border-pink-200",
};

export const BinaryHexPane: React.FC<BinaryHexPaneProps> = ({
    viewMode,
    onViewModeChange,
    hexData = "",
    sections = [],
    selectedSectionId,
    onSectionSelect
}) => {
    // Parse hex data into bytes
    const bytes: number[] = [];
    for (let i = 0; i < hexData.length; i += 2) {
        bytes.push(parseInt(hexData.substring(i, i + 2), 16));
    }

    // Helper to get matching section for a byte index
    const getSectionForByte = (index: number) => {
        // Find deepest nested section (smallest range)
        return sections
            .filter(s => index >= s.startOffset && index < s.endOffset)
            .sort((a, b) => (a.endOffset - a.startOffset) - (b.endOffset - b.startOffset))[0];
    };

    // Render a single byte value
    const renderByteValue = (byte: number, index: number) => {
        if (viewMode === 'decimal') return byte.toString().padStart(3, '0');
        if (viewMode === 'binary') return byte.toString(2).padStart(8, '0');
        return byte.toString(16).toUpperCase().padStart(2, '0');
    };

    const scrollContainerRef = React.useRef<HTMLDivElement>(null);
    const [focusedByteIndex, setFocusedByteIndex] = React.useState<number>(0);

    // Sync focused byte when external selection changes
    React.useEffect(() => {
        if (selectedSectionId && sections.length > 0) {
            const section = sections.find(s => s.id === selectedSectionId);
            if (section) {
                setFocusedByteIndex(section.startOffset);
                // Scroll into view
                const element = document.getElementById(`byte-${section.startOffset}`);
                if (element && scrollContainerRef.current) {
                    element.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
            }
        }
    }, [selectedSectionId, sections]);

    // Keyboard navigation
    const handleKeyDown = (e: React.KeyboardEvent) => {
        let newIndex = focusedByteIndex;
        const cols = 8;

        switch (e.key) {
            case 'ArrowRight': newIndex++; break;
            case 'ArrowLeft': newIndex--; break;
            case 'ArrowDown': newIndex += cols; break;
            case 'ArrowUp': newIndex -= cols; break;
            default: return; // Ignore other keys
        }

        // Clamp index
        if (newIndex < 0) newIndex = 0;
        if (newIndex >= bytes.length) newIndex = bytes.length - 1;

        setFocusedByteIndex(newIndex);
        e.preventDefault();

        // Update selection if section changed
        const newSection = getSectionForByte(newIndex);
        if (newSection && newSection.id !== selectedSectionId) {
            if (onSectionSelect) onSectionSelect(newSection.id);
        }

        // Ensure visible
        const element = document.getElementById(`byte-${newIndex}`);
        if (element) {
            element.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
    };

    // Render grid
    const renderGrid = () => {
        const rows = Math.ceil(bytes.length / 8);
        const grid = [];

        for (let r = 0; r < rows; r++) {
            const rowBytes = [];
            for (let c = 0; c < 8; c++) {
                const index = r * 8 + c;
                if (index >= bytes.length) break;

                const byte = bytes[index];
                const section = getSectionForByte(index);
                const isSelected = section && section.id === selectedSectionId;
                const isFocused = index === focusedByteIndex;

                const baseColor = section ? COLOR_MAP[section.color] || "bg-gray-50 text-gray-800" : "text-gray-400";
                const selectedClass = isSelected ? "ring-2 ring-blue-500 z-10 scale-110 shadow-sm font-bold" : "";
                const focusClass = isFocused ? "outline outline-2 outline-offset-1 outline-blue-600" : null;

                rowBytes.push(
                    <div
                        key={index}
                        id={`byte-${index}`}
                        className={`
                            px-1 rounded cursor-pointer select-none transition-all
                            text-center min-w-[2em] border border-transparent
                            ${baseColor} ${selectedClass} ${focusClass || ''}
                            hover:brightness-95
                        `}
                        onClick={() => {
                            setFocusedByteIndex(index);
                            updateSelection(section?.id);
                        }}
                        title={section ? `${section.label} (${section.type}): ${renderByteValue(byte, index)}` : `Offset ${index}`}
                    >
                        {renderByteValue(byte, index)}
                    </div>
                );
            }

            // Add spacer after 4 bytes
            if (rowBytes.length > 4) {
                rowBytes.splice(4, 0, <div key={`sep-${r}`} className="w-2" />);
            }

            grid.push(
                <div key={r} className="flex items-center mb-1">
                    {/* Offset Label */}
                    <div className="w-16 text-xs text-gray-400 font-mono text-right mr-3 select-none">
                        {(r * 8).toString(16).toUpperCase().padStart(4, '0')}:
                    </div>
                    {/* Bytes */}
                    <div className="flex gap-1 font-mono text-xs">
                        {rowBytes}
                    </div>
                </div>
            );
        }
        return grid;
    };

    // Handler to select section
    const updateSelection = (id?: string) => {
        if (onSectionSelect && id) {
            onSectionSelect(id);
        }
    };

    return (
        <div className="flex flex-col h-full bg-white">
            {/* Toolbar */}
            <div className="flex items-center justify-between px-3 py-2 border-b border-gray-200">
                <span className="text-sm font-medium text-gray-700">
                    Binary ({bytes.length} bytes)
                </span>
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
            <div
                ref={scrollContainerRef}
                className="flex-1 overflow-auto p-4 content-start outline-none"
                tabIndex={0}
                onKeyDown={handleKeyDown}
            >
                <div className="inline-block min-w-full">
                    {bytes.length > 0 ? renderGrid() : (
                        <div className="text-gray-400 italic text-center mt-10">
                            No binary data available
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};
