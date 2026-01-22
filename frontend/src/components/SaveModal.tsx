// Save Modal Component for saving and sharing playgrounds

import { Check, Copy, X } from 'lucide-react';
import React, { useState } from 'react';
import { savePlayground, type SavePlaygroundRequest } from '../services/api';

interface SaveModalProps {
    isOpen: boolean;
    onClose: () => void;
    schema: string;
    inputFormat: string;
    inputData: string;
}

export const SaveModal: React.FC<SaveModalProps> = ({
    isOpen,
    onClose,
    schema,
    inputFormat,
    inputData,
}) => {
    const [title, setTitle] = useState('');
    const [description, setDescription] = useState('');
    const [isSaving, setIsSaving] = useState(false);
    const [savedUrl, setSavedUrl] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [copiedUrl, setCopiedUrl] = useState(false);

    const handleSave = async () => {
        setIsSaving(true);
        setError(null);

        try {
            const request: SavePlaygroundRequest = {
                schema,
                input_format: inputFormat,
                input_data: inputData,
                title: title || undefined,
                description: description || undefined,
            };

            const response = await savePlayground(request);

            if (response.success) {
                // Generate full URL
                const fullUrl = `${window.location.origin}${window.location.pathname}${response.url}`;
                setSavedUrl(fullUrl);
            } else {
                setError('Failed to save playground');
            }
        } catch (err) {
            setError('An error occurred while saving');
            console.error('Save error:', err);
        } finally {
            setIsSaving(false);
        }
    };

    const copyUrl = async () => {
        if (savedUrl) {
            try {
                await navigator.clipboard.writeText(savedUrl);
                setCopiedUrl(true);
                setTimeout(() => setCopiedUrl(false), 2000);
            } catch (err) {
                console.error('Failed to copy:', err);
            }
        }
    };

    const handleClose = () => {
        setTitle('');
        setDescription('');
        setSavedUrl(null);
        setError(null);
        setCopiedUrl(false);
        onClose();
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
                {/* Header */}
                <div className="flex items-center justify-between p-4 border-b border-gray-200">
                    <h2 className="text-lg font-semibold text-gray-800">
                        {savedUrl ? 'Playground Saved!' : 'Save Playground'}
                    </h2>
                    <button
                        onClick={handleClose}
                        className="text-gray-400 hover:text-gray-600 transition-colors"
                    >
                        <X className="w-5 h-5" />
                    </button>
                </div>

                {/* Content */}
                <div className="p-4 space-y-4">
                    {!savedUrl ? (
                        <>
                            {/* Title Input */}
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    Title (optional)
                                </label>
                                <input
                                    type="text"
                                    value={title}
                                    onChange={(e) => setTitle(e.target.value)}
                                    placeholder="My Blink Message Example"
                                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    disabled={isSaving}
                                />
                            </div>

                            {/* Description Input */}
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    Description (optional)
                                </label>
                                <textarea
                                    value={description}
                                    onChange={(e) => setDescription(e.target.value)}
                                    placeholder="Describe what this playground demonstrates..."
                                    rows={3}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                                    disabled={isSaving}
                                />
                            </div>

                            {/* Error Message */}
                            {error && (
                                <div className="p-3 bg-red-50 border border-red-200 rounded-md">
                                    <p className="text-sm text-red-700">{error}</p>
                                </div>
                            )}

                            {/* Save Button */}
                            <button
                                onClick={handleSave}
                                disabled={isSaving}
                                className="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors font-medium"
                            >
                                {isSaving ? 'Saving...' : 'Save Playground'}
                            </button>
                        </>
                    ) : (
                        <>
                            {/* Success Message */}
                            <div className="p-3 bg-green-50 border border-green-200 rounded-md">
                                <p className="text-sm text-green-700">
                                    Your playground has been saved successfully!
                                </p>
                            </div>

                            {/* Shareable URL */}
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    Shareable Link
                                </label>
                                <div className="flex gap-2">
                                    <input
                                        type="text"
                                        value={savedUrl}
                                        readOnly
                                        className="flex-1 px-3 py-2 border border-gray-300 rounded-md bg-gray-50 text-sm font-mono"
                                    />
                                    <button
                                        onClick={copyUrl}
                                        className="px-3 py-2 bg-gray-100 hover:bg-gray-200 rounded-md transition-colors flex items-center gap-1.5"
                                    >
                                        {copiedUrl ? (
                                            <>
                                                <Check className="w-4 h-4 text-green-600" />
                                                <span className="text-sm text-green-600">Copied!</span>
                                            </>
                                        ) : (
                                            <>
                                                <Copy className="w-4 h-4" />
                                                <span className="text-sm">Copy</span>
                                            </>
                                        )}
                                    </button>
                                </div>
                            </div>

                            {/* Info */}
                            <p className="text-xs text-gray-500">
                                This link will be available for 30 days. Anyone with the link can view this playground.
                            </p>

                            {/* Close Button */}
                            <button
                                onClick={handleClose}
                                className="w-full px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 transition-colors font-medium"
                            >
                                Done
                            </button>
                        </>
                    )}
                </div>
            </div>
        </div>
    );
};
