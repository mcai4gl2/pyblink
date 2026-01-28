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
    rawHex?: string;
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

export interface BinarySection {
    id: string;
    type: 'header' | 'field-name' | 'field-value' | 'nested' | 'presence' | 'padding' | 'pointer' | 'data';
    startOffset: number;
    endOffset: number;
    label: string;
    dataType?: string;
    fieldPath?: string;
    rawValue?: string;
    interpretedValue?: string;
    color: string;
}

export interface MessageField {
    path: string;
    name: string;
    value: any;
    type: string;
    binarySectionId?: string;
    children?: MessageField[];
}

export interface AnalyzeBinaryRequest {
    schema: string;
    binary_hex: string;
}

export interface AnalyzeBinaryResponse {
    success: boolean;
    sections: BinarySection[];
    fields: MessageField[];
    error?: string;
    root_type?: string;
}

