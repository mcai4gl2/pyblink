// TypeScript types for the Blink Message Playground

export interface ConvertRequest {
    schema: string;
    input_format: string;
    input_data: string;
}

export interface BinaryFieldInfo {
    name: string;
    value: string | number | null;
    bytes: string;
    offset?: number;
}

export interface BinaryDecodedView {
    size: number;
    type_id: number;
    ext_offset?: number;
    fields: BinaryFieldInfo[];
}

export interface BinaryOutput {
    hex: string;
    decoded: BinaryDecodedView;
}

export interface ConvertResponse {
    success: boolean;
    outputs?: {
        tag?: string;
        json?: string;
        xml?: string;
        compact_binary?: BinaryOutput;
        native_binary?: BinaryOutput;
    };
    error?: string;
    line?: number;
    column?: number;
}

export interface ValidateSchemaRequest {
    schema: string;
}

export interface GroupInfo {
    name: string;
    type_id?: number;
    fields: Array<{ name: string; type: string }>;
}

export interface ValidateSchemaResponse {
    valid: boolean;
    groups?: GroupInfo[];
    error?: string;
    line?: number;
    column?: number;
}

export type InputFormat = 'tag' | 'json' | 'xml' | 'compact' | 'native';
