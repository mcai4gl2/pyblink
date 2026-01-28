import { Binary, Hash, Hexagon } from 'lucide-react';
import React, { useCallback, useEffect, useRef, useState } from 'react';
import { BinarySection } from '../../types';

interface BinaryHexPaneProps {
    viewMode: 'hex' | 'decimal' | 'binary';
    onViewModeChange: (mode: 'hex' | 'decimal' | 'binary') => void;
    hexData?: string;
    sections?: BinarySection[];
    selectedSectionId?: string | null;
    onSectionSelect?: (sectionId: string | null) => void;
    searchMatches?: number[];
    currentMatchByteIndex?: number;
    // Diff & Scroll Control
    scrollTop?: number;
    onScroll?: (scrollTop: number) => void;
    highlightIndices?: Set<number>;
    highlightColorClass?: string;
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

const ROW_HEIGHT = 24; // px (approximate based on styling)
const BYTES_PER_ROW = 8;
const BUFFER_ROWS = 10;

export const BinaryHexPane: React.FC<BinaryHexPaneProps> = ({
    viewMode,
    onViewModeChange,
    hexData = "",
    sections = [],
    selectedSectionId,
    onSectionSelect,
    searchMatches = [],
    currentMatchByteIndex,
    scrollTop: externalScrollTop,
    onScroll,
    highlightIndices,
    highlightColorClass
}) => {
    // Parse hex data into bytes
    const bytes: number[] = [];
    for (let i = 0; i < hexData.length; i += 2) {
        bytes.push(parseInt(hexData.substring(i, i + 2), 16));
    }

    const totalRows = Math.ceil(bytes.length / BYTES_PER_ROW);
    const totalHeight = totalRows * ROW_HEIGHT;

    // Helper to get matching section for a byte index
    const getSectionForByte = useCallback((index: number) => {
        if (!sections || sections.length === 0) return undefined;
        return sections
            .filter(s => index >= s.startOffset && index < s.endOffset)
            .sort((a, b) => (a.endOffset - a.startOffset) - (b.endOffset - b.startOffset))[0];
    }, [sections]);

    const renderByteValue = (byte: number) => {
        if (viewMode === 'decimal') return byte.toString().padStart(3, '0');
        if (viewMode === 'binary') return byte.toString(2).padStart(8, '0');
        return byte.toString(16).toUpperCase().padStart(2, '0');
    };

    const scrollContainerRef = useRef<HTMLDivElement>(null);
    const [focusedByteIndex, setFocusedByteIndex] = useState<number>(0);
    const [internalScrollTop, setInternalScrollTop] = useState(0);
    const [containerHeight, setContainerHeight] = useState(600); // Default

    // Derived scrollTop
    const currentScrollTop = externalScrollTop !== undefined ? externalScrollTop : internalScrollTop;

    // Resize observer to get container height
    useEffect(() => {
        if (!scrollContainerRef.current) return;

        const observer = new ResizeObserver(entries => {
            for (const entry of entries) {
                setContainerHeight(entry.contentRect.height);
            }
        });

        observer.observe(scrollContainerRef.current);
        return () => observer.disconnect();
    }, []);

    // Sync external scroll top to DOM
    useEffect(() => {
        if (scrollContainerRef.current && externalScrollTop !== undefined) {
            // Only update if difference is significant to avoid jitter during sync
            if (Math.abs(scrollContainerRef.current.scrollTop - externalScrollTop) > 1) {
                scrollContainerRef.current.scrollTop = externalScrollTop;
            }
        }
    }, [externalScrollTop]);

    // Scroll Handler
    const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
        const top = e.currentTarget.scrollTop;
        if (onScroll) {
            onScroll(top);
        } else {
            setInternalScrollTop(top);
        }
    };

    const scrollToByte = (index: number, align: 'center' | 'nearest') => {
        if (!scrollContainerRef.current) return;

        const row = Math.floor(index / BYTES_PER_ROW);
        const rowTop = row * ROW_HEIGHT;
        const rowBottom = rowTop + ROW_HEIGHT;
        const viewTop = currentScrollTop;
        const viewBottom = viewTop + containerHeight;

        let targetTop = viewTop;

        if (align === 'center') {
            targetTop = rowTop - (containerHeight / 2) + (ROW_HEIGHT / 2);
        } else {
            // Nearest logic
            if (rowTop < viewTop) {
                targetTop = rowTop;
            } else if (rowBottom > viewBottom) {
                targetTop = rowBottom - containerHeight;
            }
        }

        // If controlled, notify parent? 
        // scrollTo modifies DOM scrollTop.
        if (targetTop !== viewTop) {
            scrollContainerRef.current.scrollTo({ top: targetTop, behavior: 'auto' });
            // This triggers onScroll -> update state.
        }
    };

    // Sync focused byte when external selection changes
    useEffect(() => {
        if (selectedSectionId && sections.length > 0) {
            const section = sections.find(s => s.id === selectedSectionId);
            if (section) {
                setFocusedByteIndex(section.startOffset);
            }
        }
    }, [selectedSectionId, sections]);

    // Sync focused byte when search match changes
    useEffect(() => {
        if (currentMatchByteIndex !== undefined && currentMatchByteIndex >= 0) {
            setFocusedByteIndex(currentMatchByteIndex);
            scrollToByte(currentMatchByteIndex, 'center');
        }
    }, [currentMatchByteIndex]);

    // Auto-scroll logic for section selection
    useEffect(() => {
        if (selectedSectionId && focusedByteIndex >= 0) {
            const section = getSectionForByte(focusedByteIndex);
            if (section && section.id === selectedSectionId) {
                scrollToByte(focusedByteIndex, 'center');
            }
        }
    }, [selectedSectionId]);

    const handleKeyDown = (e: React.KeyboardEvent) => {
        let newIndex = focusedByteIndex;
        const cols = BYTES_PER_ROW;

        switch (e.key) {
            case 'ArrowRight': newIndex++; break;
            case 'ArrowLeft': newIndex--; break;
            case 'ArrowDown': newIndex += cols; break;
            case 'ArrowUp': newIndex -= cols; break;
            default: return; // Ignore other keys
        }

        if (newIndex < 0) newIndex = 0;
        if (newIndex >= bytes.length) newIndex = bytes.length - 1;

        setFocusedByteIndex(newIndex);
        e.preventDefault();
        scrollToByte(newIndex, 'nearest');

        const newSection = getSectionForByte(newIndex);
        if (newSection && newSection.id !== selectedSectionId) {
            if (onSectionSelect) onSectionSelect(newSection.id);
        }
    };

    const updateSelection = (id?: string) => {
        if (onSectionSelect && id) {
            onSectionSelect(id);
        }
    };

    // Calculation for virtualization
    const startIndex = Math.max(0, Math.floor(currentScrollTop / ROW_HEIGHT) - BUFFER_ROWS);
    const endIndex = Math.min(totalRows, Math.ceil((currentScrollTop + containerHeight) / ROW_HEIGHT) + BUFFER_ROWS);
    const paddingTop = startIndex * ROW_HEIGHT;
    const paddingBottom = Math.max(0, totalHeight - (endIndex * ROW_HEIGHT));

    const renderVisibleGrid = () => {
        const grid = [];
        const matchSet = new Set(searchMatches);
        // highlightIndices is Set

        for (let r = startIndex; r < endIndex; r++) {
            const rowBytes = [];
            for (let c = 0; c < 8; c++) {
                const index = r * 8 + c;
                if (index >= bytes.length) break;

                const byte = bytes[index];
                const section = getSectionForByte(index);
                const isSelected = section && section.id === selectedSectionId;
                const isFocused = index === focusedByteIndex;
                const isSearchMatch = matchSet.has(index);
                const isCurrentMatch = index === currentMatchByteIndex;
                const isHighlight = highlightIndices?.has(index);

                let baseColor = section ? COLOR_MAP[section.color] || "bg-gray-50 text-gray-800" : "text-gray-400";

                // Diff Highlight overrides all (except focus?)
                if (isHighlight && highlightColorClass) {
                    baseColor = highlightColorClass;
                }

                if (isSearchMatch) {
                    baseColor = "bg-yellow-200 text-yellow-900";
                    if (isCurrentMatch) {
                        baseColor = "bg-orange-500 text-white font-bold ring-2 ring-orange-300";
                    }
                }

                const selectedClass = (isSelected && !isCurrentMatch) ? "ring-2 ring-blue-500 z-10 scale-110 shadow-sm font-bold" : "";
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
                        title={section ? `${section.label} (${section.type}): ${renderByteValue(byte)}` : `Offset ${index}`}
                    >
                        {renderByteValue(byte)}
                    </div>
                );
            }

            if (rowBytes.length > 4) {
                rowBytes.splice(4, 0, <div key={`sep-${r}`} className="w-2" />);
            }

            grid.push(
                <div key={r} className="flex items-center" style={{ height: ROW_HEIGHT }}>
                    <div className="w-16 text-xs text-gray-400 font-mono text-right mr-3 select-none">
                        {(r * 8).toString(16).toUpperCase().padStart(4, '0')}:
                    </div>
                    <div className="flex gap-1 font-mono text-xs items-center h-full">
                        {rowBytes}
                    </div>
                </div>
            );
        }
        return grid;
    };

    return (
        <div className="flex flex-col h-full bg-white">
            <div className="flex items-center justify-between px-3 py-2 border-b border-gray-200 shrink-0">
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

            <div
                ref={scrollContainerRef}
                className="flex-1 overflow-auto p-4 content-start outline-none"
                tabIndex={0}
                onKeyDown={handleKeyDown}
                onScroll={handleScroll}
            >
                <div className="inline-block min-w-full relative">
                    <div style={{ height: paddingTop }} />
                    {bytes.length > 0 ? renderVisibleGrid() : (
                        <div className="text-gray-400 italic text-center mt-10">
                            No binary data available
                        </div>
                    )}
                    {bytes.length > 0 && <div style={{ height: paddingBottom }} />}
                </div>
            </div>
        </div>
    );
};
