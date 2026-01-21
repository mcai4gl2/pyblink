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
