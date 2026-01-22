// API service for communicating with the backend

import axios from 'axios';
import type {
    ConvertRequest,
    ConvertResponse,
    ValidateSchemaRequest,
    ValidateSchemaResponse,
} from '../types';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000';

const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

export const convertMessage = async (
    request: ConvertRequest
): Promise<ConvertResponse> => {
    try {
        const response = await api.post<ConvertResponse>('/api/convert', request);
        return response.data;
    } catch (error) {
        if (axios.isAxiosError(error) && error.response) {
            return error.response.data;
        }
        throw error;
    }
};

export const validateSchema = async (
    request: ValidateSchemaRequest
): Promise<ValidateSchemaResponse> => {
    try {
        const response = await api.post<ValidateSchemaResponse>(
            '/api/validate-schema',
            request
        );
        return response.data;
    } catch (error) {
        if (axios.isAxiosError(error) && error.response) {
            return error.response.data;
        }
        throw error;
    }
};

export const checkHealth = async (): Promise<{ status: string }> => {
    const response = await api.get('/health');
    return response.data;
};

export interface SavePlaygroundRequest {
    schema: string;
    input_format: string;
    input_data: string;
    title?: string;
    description?: string;
}

export interface SavePlaygroundResponse {
    success: boolean;
    playground_id: string;
    url: string;
    message: string;
}

export interface LoadPlaygroundResponse {
    success: boolean;
    playground?: {
        id: string;
        schema: string;
        input_format: string;
        input_data: string;
        title?: string;
        description?: string;
        created_at: string;
    };
    error?: string;
}

export const savePlayground = async (
    request: SavePlaygroundRequest
): Promise<SavePlaygroundResponse> => {
    try {
        const response = await api.post<SavePlaygroundResponse>('/api/save', request);
        return response.data;
    } catch (error) {
        if (axios.isAxiosError(error) && error.response) {
            return error.response.data;
        }
        throw error;
    }
};

export const loadPlayground = async (
    playgroundId: string
): Promise<LoadPlaygroundResponse> => {
    try {
        const response = await api.get<LoadPlaygroundResponse>(`/api/load/${playgroundId}`);
        return response.data;
    } catch (error) {
        if (axios.isAxiosError(error) && error.response) {
            return error.response.data;
        }
        throw error;
    }
};

