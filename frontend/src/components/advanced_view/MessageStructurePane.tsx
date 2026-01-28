import { Braces, ChevronRight, Circle, Tag } from 'lucide-react';
import React from 'react';
import { MessageField } from '../../types';

interface MessageStructurePaneProps {
    format: 'json' | 'tag';
    onFormatChange: (format: 'json' | 'tag') => void;
    fields?: MessageField[];
    selectedSectionId?: string | null;
    onFieldSelect?: (sectionId: string | null) => void;
}

export const MessageStructurePane: React.FC<MessageStructurePaneProps> = ({
    format,
    onFormatChange,
    fields = [],
    selectedSectionId,
    onFieldSelect
}) => {

    const scrollContainerRef = React.useRef<HTMLDivElement>(null);

    // Scroll to selected field
    React.useEffect(() => {
        if (selectedSectionId && scrollContainerRef.current) {
            const element = document.getElementById(`field-${selectedSectionId}`);
            if (element) {
                element.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        }
    }, [selectedSectionId]);

    const renderField = (field: MessageField, index: number) => {
        const isSelected = field.binarySectionId === selectedSectionId;
        const depth = field.path.split('.').length - 1;

        return (
            <div
                key={index}
                id={field.binarySectionId ? `field-${field.binarySectionId}` : undefined}
                className={`
                    flex items-center gap-2 px-2 py-1 rounded cursor-pointer transition-colors
                    ${isSelected ? 'bg-blue-100 ring-1 ring-blue-300' : 'hover:bg-gray-100'}
                `}
                style={{ marginLeft: `${depth * 16}px` }}
                onClick={() => onFieldSelect && onFieldSelect(field.binarySectionId || null)}
            >
                {field.type === 'object' ? (
                    <ChevronRight className="w-3 h-3 text-gray-400" />
                ) : (
                    <Circle className="w-2 h-2 text-gray-300 fill-current" />
                )}

                <span className="text-purple-700 font-medium">"{field.name}"</span>
                <span className="text-gray-500">:</span>
                <span className={`
                    truncate
                    ${field.type === 'string' ? 'text-green-600' : ''}
                    ${field.type === 'i32' || field.type === 'u32' || field.type === 'i64' || field.type === 'u64' ? 'text-orange-600' : ''}
                    ${field.type === 'bool' ? 'text-blue-600' : ''}
                `}>
                    {field.type === 'string' ? `"${field.value}"` : String(field.value)}
                </span>

                {field.type !== 'object' && (
                    <span className="text-xs text-gray-400 ml-auto">{field.type}</span>
                )}
            </div>
        );
    };

    return (
        <div className="flex flex-col h-full bg-white">
            {/* Toolbar */}
            <div className="flex items-center justify-between px-3 py-2 border-b border-gray-200">
                <span className="text-sm font-medium text-gray-700">Message Structure</span>
                <div className="flex bg-gray-100 rounded p-0.5">
                    <button
                        onClick={() => onFormatChange('json')}
                        className={`px-2 py-1 text-xs font-medium rounded flex items-center gap-1.5 transition-all
                            ${format === 'json' ? 'bg-white text-blue-600 shadow-sm' : 'text-gray-500 hover:text-gray-700'}`}
                    >
                        <Braces className="w-3.5 h-3.5" />
                        Structure
                    </button>
                    {/* Tag format placeholder/toggle - keeping it as requested but it renders same structure for now */}
                    <button
                        onClick={() => onFormatChange('tag')}
                        className={`px-2 py-1 text-xs font-medium rounded flex items-center gap-1.5 transition-all
                            ${format === 'tag' ? 'bg-white text-blue-600 shadow-sm' : 'text-gray-500 hover:text-gray-700'}`}
                    >
                        <Tag className="w-3.5 h-3.5" />
                        Tag
                    </button>
                </div>
            </div>

            {/* Content Area */}
            <div
                ref={scrollContainerRef}
                className="flex-1 overflow-auto p-4 font-mono text-sm"
            >
                {fields.length > 0 ? (
                    <div className="flex flex-col gap-0.5">
                        {fields.map((field, i) => renderField(field, i))}
                    </div>
                ) : (
                    <div className="text-gray-400 italic">
                        No fields analyzed yet.
                    </div>
                )}
            </div>
        </div>
    );
};
