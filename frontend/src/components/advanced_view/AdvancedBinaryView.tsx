import { ArrowDown, ArrowUp, FileDiff, FileJson, Hash, Layout, Maximize2, Minimize2, Search, X } from 'lucide-react';
import React, { useEffect, useMemo, useState } from 'react';
import { analyzeBinary, convertMessage } from '../../services/api';
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
    const [rootTypeName, setRootTypeName] = useState<string | undefined>(undefined);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [selectedSectionId, setSelectedSectionId] = useState<string | null>(null);

    // State for toggles
    const [structureFormat, setStructureFormat] = useState<'json' | 'tag'>('json');
    const [viewMode, setViewMode] = useState<'hex' | 'decimal' | 'binary'>('hex');

    // Search State
    const [isSearchOpen, setIsSearchOpen] = useState(false);
    const [searchText, setSearchText] = useState("");
    const [isHexSearch, setIsHexSearch] = useState(false);
    const [searchMatches, setSearchMatches] = useState<number[]>([]);
    const [currentMatchIdx, setCurrentMatchIdx] = useState(-1);

    // Help Modal State
    const [isHelpOpen, setIsHelpOpen] = useState(false);

    // Diff Feature State
    const [isDiffMode, setIsDiffMode] = useState(false);
    const [diffHexData, setDiffHexData] = useState<string>("");
    const [isDiffPromptOpen, setIsDiffPromptOpen] = useState(false);
    const [diffInput, setDiffInput] = useState("");
    const [diffInputType, setDiffInputType] = useState<'hex' | 'json'>('hex');
    const [sharedScrollTop, setSharedScrollTop] = useState(0);
    const [isDiffConverting, setIsDiffConverting] = useState(false);

    // Global Shortcuts
    useEffect(() => {
        const handleGlobalKeyDown = (e: KeyboardEvent) => {
            if (!isOpen) return;

            // Ctrl+F or Cmd+F
            if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'f') {
                e.preventDefault();
                setIsSearchOpen(true);
                setTimeout(() => document.getElementById('search-input')?.focus(), 0);
                return;
            }

            // Esc
            if (e.key === 'Escape') {
                if (isHelpOpen) setIsHelpOpen(false);
                else if (isDiffPromptOpen) setIsDiffPromptOpen(false);
                else if (isSearchOpen) setIsSearchOpen(false);
                else onClose();
            }

            // ? for Help
            if (e.key === '?' && !isSearchOpen && !isHelpOpen && !isDiffPromptOpen) {
                if (document.activeElement?.tagName !== 'INPUT' && document.activeElement?.tagName !== 'TEXTAREA') {
                    setIsHelpOpen(true);
                }
            }
        };

        window.addEventListener('keydown', handleGlobalKeyDown);
        return () => window.removeEventListener('keydown', handleGlobalKeyDown);
    }, [isOpen, isSearchOpen, isHelpOpen, isDiffPromptOpen, onClose]);

    // Fetch analysis when opened or data changes
    useEffect(() => {
        if (isOpen && schema && cleanHexData) {
            fetchAnalysis();
        } else {
            // Reset if closed or empty
            if (!isOpen) {
                setSections([]);
                setFields([]);
                setRootTypeName(undefined);
                setError(null);
                setSelectedSectionId(null);
                // Reset search
                setSearchText("");
                setSearchMatches([]);
                setIsSearchOpen(false);
                // Reset Diff
                setIsDiffMode(false);
                setDiffHexData("");
                setDiffInput("");
            }
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [isOpen, schema, cleanHexData]);

    const fetchAnalysis = async () => {
        setIsLoading(true);
        setError(null);
        try {
            const response = await analyzeBinary({ schema, binary_hex: cleanHexData });
            if (response.success) {
                setSections(response.sections);
                setFields(response.fields);
                setRootTypeName(response.root_type);
            } else {
                setError(response.error || "Analysis failed");
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to analyze binary");
        } finally {
            setIsLoading(false);
        }
    };

    const handleStartDiff = async () => {
        if (diffInputType === 'hex') {
            setDiffHexData(diffInput);
            setIsDiffMode(true);
            setIsDiffPromptOpen(false);
        } else {
            // Convert JSON to Hex
            setIsDiffConverting(true);
            try {
                let jsonData = diffInput.trim();

                // If it looks like JSON but missing type, try to inject it
                if (rootTypeName && jsonData.startsWith('{') && !jsonData.includes('"$type"')) {
                    // Simple injection attempt, assumes simple object
                    // We parse it first to be safe
                    try {
                        const parsed = JSON.parse(jsonData);
                        if (!parsed.$type) {
                            parsed.$type = rootTypeName;
                            jsonData = JSON.stringify(parsed);
                        }
                    } catch (e) {
                        // Ignore parse error here, let backend or convert handle it
                    }
                }

                const response = await convertMessage({
                    schema,
                    input_format: 'json',
                    input_data: jsonData
                });

                if (response.success && response.outputs?.native_binary) {
                    const hexCallback = response.outputs.native_binary.rawHex || response.outputs.native_binary.hex;
                    setDiffHexData(hexCallback);
                    setIsDiffMode(true);
                    setIsDiffPromptOpen(false);
                } else {
                    alert("Conversion failed: " + (response.error || "Unknown error"));
                }
            } catch (e) {
                alert("Error connecting to backend");
            } finally {
                setIsDiffConverting(false);
            }
        }
    };

    // Calculate Diffs
    const diffIndices = useMemo(() => {
        if (!isDiffMode || !cleanHexData || !diffHexData) return new Set<number>();

        const cleanDiff = diffHexData.replace(/[^0-9A-Fa-f]/g, '');
        const indices = new Set<number>();

        const lenA = cleanHexData.length / 2; // bytes
        const lenB = cleanDiff.length / 2;
        const maxLen = Math.max(lenA, lenB);

        for (let i = 0; i < maxLen; i++) {
            // Get byte strings
            const byteA = cleanHexData.substring(i * 2, i * 2 + 2).toLowerCase();
            const byteB = cleanDiff.substring(i * 2, i * 2 + 2).toLowerCase();

            if (i >= lenA || i >= lenB) {
                indices.add(i); // Length mismatch
            } else if (byteA !== byteB) {
                indices.add(i); // Content mismatch
            }
        }
        return indices;
    }, [isDiffMode, cleanHexData, diffHexData]);

    // Search Logic (Occurrences)
    const [matchOccurrences, setMatchOccurrences] = useState<number[]>([]);

    useEffect(() => {
        if (!searchText) {
            setSearchMatches([]);
            setMatchOccurrences([]);
            setCurrentMatchIdx(-1);
            return;
        }

        let searchHex = "";
        // Search always targets Original data

        if (isHexSearch) {
            searchHex = searchText.replace(/[^0-9A-Fa-f]/g, '');
        } else {
            const encoder = new TextEncoder();
            const bytes = encoder.encode(searchText);
            searchHex = Array.from(bytes).map(b => b.toString(16).padStart(2, '0')).join('');
        }

        if (!searchHex) {
            setSearchMatches([]);
            setMatchOccurrences([]);
            return;
        }

        const occurrences: number[] = [];
        const allMatchBytes: number[] = [];

        const target = searchHex.toLowerCase();
        const source = cleanHexData.toLowerCase();

        let pos = source.indexOf(target);
        const byteLen = Math.ceil(target.length / 2);

        while (pos !== -1) {
            if (pos % 2 === 0) {
                const byteIdx = pos / 2;
                occurrences.push(byteIdx);
                for (let i = 0; i < byteLen; i++) allMatchBytes.push(byteIdx + i);
            }
            pos = source.indexOf(target, pos + 2);
        }

        setMatchOccurrences(occurrences);
        setSearchMatches(allMatchBytes);

        if (occurrences.length > 0) {
            setCurrentMatchIdx(0);
        } else {
            setCurrentMatchIdx(-1);
        }

    }, [searchText, isHexSearch, cleanHexData]);

    const nextMatch = () => {
        if (matchOccurrences.length === 0) return;
        setCurrentMatchIdx((prev) => (prev + 1) % matchOccurrences.length);
    };

    const prevMatch = () => {
        if (matchOccurrences.length === 0) return;
        setCurrentMatchIdx((prev) => (prev - 1 + matchOccurrences.length) % matchOccurrences.length);
    };

    // Search Keys
    useEffect(() => {
        const handleSearchKeys = (e: KeyboardEvent) => {
            if (!isSearchOpen || matchOccurrences.length === 0) return;
            if (e.key === 'Enter') {
                e.preventDefault();
                if (e.shiftKey) prevMatch();
                else nextMatch();
            }
        };
        window.addEventListener('keydown', handleSearchKeys);
        return () => window.removeEventListener('keydown', handleSearchKeys);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [isSearchOpen, matchOccurrences.length]);

    if (!isOpen) return null;

    const toggleMaximize = () => setIsMaximized(!isMaximized);
    const selectedSection = sections.find(s => s.id === selectedSectionId);

    // Determine current focused byte for BinaryHexPane
    const currentSearchFocus = matchOccurrences.length > 0 && currentMatchIdx >= 0
        ? matchOccurrences[currentMatchIdx]
        : undefined;

    return (
        <div className={`fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm transition-all duration-300 ${isOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'}`}>
            <div className={`bg-white rounded-lg shadow-2xl flex flex-col transition-all duration-300 ${isMaximized ? 'w-full h-full' : 'w-[90vw] h-[85vh] max-w-7xl'}`}>

                {/* Header */}
                <header className="flex items-center justify-between px-4 py-3 border-b border-gray-200 bg-gray-50 rounded-t-lg">
                    <div className="flex items-center gap-4">
                        <div className="flex items-center gap-2">
                            <Layout className="w-5 h-5 text-blue-600" />
                            <h2 className="text-lg font-semibold text-gray-800">Advanced Binary Inspector</h2>
                            {isLoading && <span className="text-xs text-gray-500 animate-pulse ml-2">Analyzing...</span>}
                            {error && <span className="text-xs text-red-500 ml-2">Error: {error}</span>}
                        </div>

                        {/* Search Toolbar */}
                        <div className={`flex items-center gap-2 transition-all overflow-hidden ${isSearchOpen ? 'w-96 opacity-100' : 'w-0 opacity-0'}`}>
                            <div className="flex items-center bg-white border border-gray-300 rounded-md px-2 py-1 shadow-sm focus-within:ring-2 focus-within:ring-blue-500 focus-within:border-blue-500">
                                <Search className="w-4 h-4 text-gray-400 mr-2" />
                                <input
                                    id="search-input"
                                    type="text"
                                    className="w-full text-sm outline-none bg-transparent"
                                    placeholder={isHexSearch ? "Search hex (e.g. 41 42)" : "Search text..."}
                                    value={searchText}
                                    onChange={(e) => setSearchText(e.target.value)}
                                />
                                <span className="text-xs text-gray-400 whitespace-nowrap px-1 border-l border-gray-200 ml-1">
                                    {matchOccurrences.length > 0 ? `${currentMatchIdx + 1}/${matchOccurrences.length}` : '0/0'}
                                </span>
                            </div>

                            <div className="flex bg-gray-200 rounded p-0.5 shrink-0">
                                <button onClick={prevMatch} disabled={matchOccurrences.length === 0} className="p-1 hover:bg-white rounded text-gray-600 disabled:opacity-50">
                                    <ArrowUp className="w-3 h-3" />
                                </button>
                                <button onClick={nextMatch} disabled={matchOccurrences.length === 0} className="p-1 hover:bg-white rounded text-gray-600 disabled:opacity-50">
                                    <ArrowDown className="w-3 h-3" />
                                </button>
                            </div>

                            <button
                                onClick={() => setIsHexSearch(!isHexSearch)}
                                className={`text-xs px-2 py-1 rounded border ${isHexSearch ? 'bg-blue-100 text-blue-700 border-blue-200' : 'bg-white text-gray-600 border-gray-200 hover:bg-gray-50'}`}
                                title="Toggle Hex Search"
                            >
                                Hex
                            </button>
                        </div>
                    </div>

                    <div className="flex items-center gap-2">
                        {/* Diff Button */}
                        <button
                            onClick={() => {
                                if (isDiffMode) {
                                    setIsDiffMode(false);
                                } else {
                                    setIsDiffPromptOpen(true);
                                }
                            }}
                            className={`p-1.5 rounded transition-colors ${isDiffMode ? 'bg-purple-100 text-purple-600' : 'text-gray-500 hover:text-purple-600 hover:bg-purple-50'}`}
                            title="Diff / Compare Mode"
                        >
                            <FileDiff className="w-4 h-4" />
                        </button>

                        <button
                            onClick={() => setIsHelpOpen(true)}
                            className="p-1.5 text-gray-500 hover:text-gray-700 hover:bg-gray-200 rounded transition-colors text-xs font-bold w-7 h-7 flex items-center justify-center"
                            title="Keyboard Shortcuts (?)"
                        >
                            ?
                        </button>

                        <button
                            onClick={() => {
                                setIsSearchOpen(!isSearchOpen);
                                if (!isSearchOpen) setTimeout(() => document.getElementById('search-input')?.focus(), 50);
                            }}
                            className={`p-1.5 rounded transition-colors ${isSearchOpen ? 'bg-blue-100 text-blue-600' : 'text-gray-500 hover:text-gray-700 hover:bg-gray-200'}`}
                            title="Toggle Search (Ctrl+F)"
                        >
                            <Search className="w-4 h-4" />
                        </button>

                        <div className="w-px h-6 bg-gray-300 mx-1"></div>

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
                <div className="flex-1 flex overflow-hidden relative">
                    {/* Help Modal */}
                    {isHelpOpen && (
                        <div className="absolute inset-0 z-50 bg-black/20 flex items-center justify-center backdrop-blur-[1px]" onClick={() => setIsHelpOpen(false)}>
                            <div className="bg-white rounded-lg shadow-xl p-6 w-96 max-w-full" onClick={e => e.stopPropagation()}>
                                <div className="flex justify-between items-center mb-4">
                                    <h3 className="text-lg font-bold text-gray-800">Keyboard Shortcuts</h3>
                                    <button onClick={() => setIsHelpOpen(false)} className="text-gray-400 hover:text-gray-600"><X className="w-5 h-5" /></button>
                                </div>
                                <div className="space-y-3">
                                    <div className="flex justify-between text-sm"><span className="text-gray-600">Toggle Search</span><kbd className="bg-gray-100 border border-gray-300 rounded px-2 font-mono text-xs py-0.5">Ctrl + F</kbd></div>
                                    <div className="flex justify-between text-sm"><span className="text-gray-600">Navigate Bytes</span><kbd className="bg-gray-100 border border-gray-300 rounded px-2 font-mono text-xs py-0.5">Arrows</kbd></div>
                                    <div className="flex justify-between text-sm"><span className="text-gray-600">Next Match</span><kbd className="bg-gray-100 border border-gray-300 rounded px-2 font-mono text-xs py-0.5">Enter</kbd></div>
                                    <div className="flex justify-between text-sm"><span className="text-gray-600">Previous Match</span><kbd className="bg-gray-100 border border-gray-300 rounded px-2 font-mono text-xs py-0.5">Shift + Enter</kbd></div>
                                    <div className="flex justify-between text-sm"><span className="text-gray-600">Close / Exit</span><kbd className="bg-gray-100 border border-gray-300 rounded px-2 font-mono text-xs py-0.5">Esc</kbd></div>
                                    <div className="flex justify-between text-sm"><span className="text-gray-600">Help</span><kbd className="bg-gray-100 border border-gray-300 rounded px-2 font-mono text-xs py-0.5">?</kbd></div>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Diff Input Modal */}
                    {isDiffPromptOpen && (
                        <div className="absolute inset-0 z-50 bg-black/20 flex items-center justify-center backdrop-blur-[1px]" onClick={() => setIsDiffPromptOpen(false)}>
                            <div className="bg-white rounded-lg shadow-xl p-6 w-[32rem] max-w-full" onClick={e => e.stopPropagation()}>
                                <div className="flex justify-between items-center mb-4">
                                    <h3 className="text-lg font-bold text-gray-800">Compare Binary Data</h3>
                                    <button onClick={() => setIsDiffPromptOpen(false)} className="text-gray-400 hover:text-gray-600"><X className="w-5 h-5" /></button>
                                </div>

                                {/* Tabs */}
                                <div className="flex gap-2 mb-3 border-b border-gray-200">
                                    <button
                                        className={`pb-2 px-1 text-sm font-medium border-b-2 transition-colors flex items-center gap-1.5 ${diffInputType === 'hex' ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'}`}
                                        onClick={() => setDiffInputType('hex')}
                                    >
                                        <Hash className="w-3.5 h-3.5" /> Hex String
                                    </button>
                                    <button
                                        className={`pb-2 px-1 text-sm font-medium border-b-2 transition-colors flex items-center gap-1.5 ${diffInputType === 'json' ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'}`}
                                        onClick={() => setDiffInputType('json')}
                                    >
                                        <FileJson className="w-3.5 h-3.5" /> JSON Input
                                    </button>
                                </div>

                                <div className="mb-4">
                                    <label htmlFor="diff-input" className="block text-sm font-medium text-gray-700 mb-1">
                                        {diffInputType === 'hex' ? 'Paste Hex Data:' : 'Paste JSON Object:'}
                                    </label>
                                    <textarea
                                        id="diff-input"
                                        className="w-full h-40 border border-gray-300 rounded-md p-2 font-mono text-xs resize-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 outline-none"
                                        placeholder={diffInputType === 'hex' ? "0A 1B 2C ..." : "{\n  \"field\": \"value\"\n}"}
                                        value={diffInput}
                                        onChange={(e) => setDiffInput(e.target.value)}
                                        autoFocus
                                    />
                                    {diffInputType === 'json' && rootTypeName && (
                                        <p className="text-xs text-gray-500 mt-1">
                                            JSON will be auto-converted to Native Binary using type <b>{rootTypeName}</b> if not specified.
                                        </p>
                                    )}
                                </div>
                                <div className="flex justify-end gap-2">
                                    <button onClick={() => setIsDiffPromptOpen(false)} className="px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-100 rounded">Cancel</button>
                                    <button
                                        onClick={handleStartDiff}
                                        disabled={isDiffConverting || !diffInput}
                                        className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 shadow-sm disabled:opacity-50 flex items-center gap-2"
                                    >
                                        {isDiffConverting ? 'Converting...' : 'Compare'}
                                    </button>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* View Modes */}
                    {isDiffMode ? (
                        <div className="flex-1 flex overflow-hidden">
                            {/* Left Pane (Ref / Original) */}
                            <div className="w-1/2 border-r border-gray-200 flex flex-col min-w-[300px]">
                                <div className="px-3 py-1 bg-gray-100 border-b border-gray-200 text-xs font-semibold text-gray-600 flex justify-between">
                                    <span>Original</span>
                                    <span>{diffIndices.size} Differences</span>
                                </div>
                                <BinaryHexPane
                                    viewMode={viewMode}
                                    onViewModeChange={setViewMode}
                                    hexData={cleanHexData}
                                    sections={sections}
                                    selectedSectionId={selectedSectionId}
                                    onSectionSelect={setSelectedSectionId}
                                    searchMatches={searchMatches}
                                    currentMatchByteIndex={currentSearchFocus}
                                    scrollTop={sharedScrollTop}
                                    onScroll={setSharedScrollTop}
                                    highlightIndices={diffIndices}
                                    highlightColorClass="bg-red-200 text-red-900 border-red-300"
                                />
                            </div>

                            {/* Right Pane (Compare / Target) */}
                            <div className="w-1/2 flex flex-col min-w-[300px]">
                                <div className="px-3 py-1 bg-gray-100 border-b border-gray-200 text-xs font-semibold text-gray-600">
                                    Comparison Target
                                </div>
                                <BinaryHexPane
                                    viewMode={viewMode}
                                    onViewModeChange={setViewMode}
                                    hexData={diffHexData ? diffHexData.replace(/[^0-9A-Fa-f]/g, '') : ""}
                                    // No sections for target? Or assume same schema? 
                                    // If same schema, offsets might not match if len differs. So pass empty sections or careful?
                                    // Pass empty for safe display. Or sections if strict match.
                                    sections={[]}
                                    // Sync scroll
                                    scrollTop={sharedScrollTop}
                                    onScroll={setSharedScrollTop}
                                    highlightIndices={diffIndices}
                                    highlightColorClass="bg-red-200 text-red-900 border-red-300" // Or Green?
                                />
                            </div>
                        </div>
                    ) : (
                        <div className="flex-1 flex overflow-hidden">
                            {/* Standard Split View */}
                            <div className="w-1/2 border-r border-gray-200 flex flex-col min-w-[300px]">
                                <MessageStructurePane
                                    format={structureFormat}
                                    onFormatChange={setStructureFormat}
                                    fields={fields}
                                    onFieldSelect={(id) => setSelectedSectionId(id)}
                                    selectedSectionId={selectedSectionId}
                                />
                            </div>

                            <div className="w-1/2 flex flex-col min-w-[300px]">
                                <BinaryHexPane
                                    viewMode={viewMode}
                                    onViewModeChange={setViewMode}
                                    hexData={cleanHexData}
                                    sections={sections}
                                    selectedSectionId={selectedSectionId}
                                    onSectionSelect={setSelectedSectionId}
                                    searchMatches={searchMatches}
                                    currentMatchByteIndex={currentSearchFocus}
                                />
                            </div>
                        </div>
                    )}
                </div>

                {/* Bottom Panel - Byte Analysis (Always visible? Or maybe confusing in Diff Mode?) */}
                {/* In Diff Mode, selection works on Left Pane. Byte Analysis can show Left Pane Value. */}
                <div className="h-48 border-t border-gray-200 bg-gray-50 shrink-0">
                    <ByteAnalysisPanel section={selectedSection} hexData={cleanHexData} />
                </div>
            </div>
        </div>
    );
};
