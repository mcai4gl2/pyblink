// Toast Notification Component for user feedback

import { AlertCircle, CheckCircle, Info, X, XCircle } from 'lucide-react';
import React, { useEffect } from 'react';

export type ToastType = 'success' | 'error' | 'info' | 'warning';

export interface Toast {
    id: string;
    type: ToastType;
    message: string;
    duration?: number;
}

interface ToastContainerProps {
    toasts: Toast[];
    onRemove: (id: string) => void;
}

export const ToastContainer: React.FC<ToastContainerProps> = ({ toasts, onRemove }) => {
    return (
        <div className="fixed top-4 right-4 z-50 space-y-2">
            {toasts.map((toast) => (
                <ToastItem key={toast.id} toast={toast} onRemove={onRemove} />
            ))}
        </div>
    );
};

interface ToastItemProps {
    toast: Toast;
    onRemove: (id: string) => void;
}

const ToastItem: React.FC<ToastItemProps> = ({ toast, onRemove }) => {
    useEffect(() => {
        const duration = toast.duration || 3000;
        const timer = setTimeout(() => {
            onRemove(toast.id);
        }, duration);

        return () => clearTimeout(timer);
    }, [toast, onRemove]);

    const getIcon = () => {
        switch (toast.type) {
            case 'success':
                return <CheckCircle className="w-5 h-5 text-green-600" />;
            case 'error':
                return <XCircle className="w-5 h-5 text-red-600" />;
            case 'warning':
                return <AlertCircle className="w-5 h-5 text-yellow-600" />;
            case 'info':
                return <Info className="w-5 h-5 text-blue-600" />;
        }
    };

    const getBackgroundColor = () => {
        switch (toast.type) {
            case 'success':
                return 'bg-green-50 border-green-200';
            case 'error':
                return 'bg-red-50 border-red-200';
            case 'warning':
                return 'bg-yellow-50 border-yellow-200';
            case 'info':
                return 'bg-blue-50 border-blue-200';
        }
    };

    const getTextColor = () => {
        switch (toast.type) {
            case 'success':
                return 'text-green-800';
            case 'error':
                return 'text-red-800';
            case 'warning':
                return 'text-yellow-800';
            case 'info':
                return 'text-blue-800';
        }
    };

    return (
        <div
            className={`flex items-center gap-3 px-4 py-3 rounded-lg shadow-lg border ${getBackgroundColor()} min-w-[300px] max-w-md animate-slide-in`}
        >
            {getIcon()}
            <p className={`flex-1 text-sm font-medium ${getTextColor()}`}>
                {toast.message}
            </p>
            <button
                onClick={() => onRemove(toast.id)}
                className="text-gray-400 hover:text-gray-600 transition-colors"
            >
                <X className="w-4 h-4" />
            </button>
        </div>
    );
};

// Hook for managing toasts
export const useToast = () => {
    const [toasts, setToasts] = React.useState<Toast[]>([]);

    const addToast = (type: ToastType, message: string, duration?: number) => {
        const id = Math.random().toString(36).substring(7);
        const toast: Toast = { id, type, message, duration };
        setToasts((prev) => [...prev, toast]);
    };

    const removeToast = (id: string) => {
        setToasts((prev) => prev.filter((toast) => toast.id !== id));
    };

    const showSuccess = (message: string, duration?: number) => {
        addToast('success', message, duration);
    };

    const showError = (message: string, duration?: number) => {
        addToast('error', message, duration);
    };

    const showInfo = (message: string, duration?: number) => {
        addToast('info', message, duration);
    };

    const showWarning = (message: string, duration?: number) => {
        addToast('warning', message, duration);
    };

    return {
        toasts,
        removeToast,
        showSuccess,
        showError,
        showInfo,
        showWarning,
    };
};
