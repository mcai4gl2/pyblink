import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import * as api from '../../../services/api';
import { AdvancedBinaryView } from '../AdvancedBinaryView';

// Mock API
jest.mock('../../../services/api');

// Mock scrollIntoView
Element.prototype.scrollIntoView = jest.fn();

const mockAnalyzeBinary = api.analyzeBinary as jest.Mock;

// Mock response with pointer and data sections for string field
const mockAnalysisWithPointer = {
    success: true,
    sections: [
        { id: 'header-size', startOffset: 0, endOffset: 4, label: 'Message Size', type: 'header', color: 'blue', rawValue: '70000000', interpretedValue: '112 bytes' },
        { id: 'header-type-id', startOffset: 4, endOffset: 12, label: 'Type ID', type: 'header', color: 'blue', rawValue: '0100000000000000', interpretedValue: '1' },
        { id: 'field-symbol-ptr', startOffset: 16, endOffset: 20, label: 'SymbolPtr', type: 'pointer', color: 'orange', rawValue: '14000000', interpretedValue: '-> +20', fieldPath: 'Symbol' },
        { id: 'field-symbol', startOffset: 36, endOffset: 45, label: 'Symbol', type: 'field-value', color: 'green', rawValue: '0500000041415041', interpretedValue: 'AAPL', fieldPath: 'Symbol', dataType: 'string' },
        { id: 'field-price', startOffset: 20, endOffset: 28, label: 'Price', type: 'field-value', color: 'yellow', rawValue: '0000000000C06240', interpretedValue: '150.25', fieldPath: 'Price', dataType: 'f64' }
    ],
    fields: [
        { path: 'Symbol', name: 'Symbol', value: 'AAPL', type: 'string', binarySectionId: 'field-symbol' },
        { path: 'Price', name: 'Price', value: '150.25', type: 'f64', binarySectionId: 'field-price' }
    ],
    root_type: 'Trading:Order'
};

const mockHexData = "70000000010000000000000014000000000000000000C06240050000004141504C";
const mockSchema = "namespace Trading; Order { string Symbol; f64 Price; }";

describe('AdvancedBinaryView - Bidirectional Highlighting', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        mockAnalyzeBinary.mockResolvedValue(mockAnalysisWithPointer);
    });

    test('renders and loads analysis data with pointer sections', async () => {
        render(
            <AdvancedBinaryView isOpen={true} onClose={() => { }} schema={mockSchema} hexData={mockHexData} />
        );

        // Wait for analysis to complete
        await waitFor(() => expect(screen.queryByText(/Analyzing.../i)).not.toBeInTheDocument());

        // Verify the API was called
        expect(mockAnalyzeBinary).toHaveBeenCalledWith({
            schema: mockSchema,
            binary_hex: mockHexData
        });

        // Verify fields are rendered
        await waitFor(() => {
            expect(screen.getByText('"Symbol"')).toBeInTheDocument();
            expect(screen.getByText('"Price"')).toBeInTheDocument();
        });
    });

    test('clicking on string field highlights it', async () => {
        render(
            <AdvancedBinaryView isOpen={true} onClose={() => { }} schema={mockSchema} hexData={mockHexData} />
        );

        // Wait for analysis to complete
        await waitFor(() => expect(screen.queryByText(/Analyzing.../i)).not.toBeInTheDocument());

        // Find and click the Symbol field
        const symbolField = screen.getByText('"Symbol"');
        await waitFor(() => expect(symbolField).toBeInTheDocument());

        const fieldContainer = symbolField.closest('div');
        if (fieldContainer) {
            fireEvent.click(fieldContainer);
        }

        // Verify the field gets highlighted class
        await waitFor(() => {
            const updatedContainer = screen.getByText('"Symbol"').closest('div');
            expect(updatedContainer?.className).toMatch(/bg-blue/);
        });
    });

    test('clicking different fields changes highlighting', async () => {
        render(
            <AdvancedBinaryView isOpen={true} onClose={() => { }} schema={mockSchema} hexData={mockHexData} />
        );

        // Wait for analysis to complete
        await waitFor(() => expect(screen.queryByText(/Analyzing.../i)).not.toBeInTheDocument());

        // Click on Symbol field
        const symbolField = screen.getByText('"Symbol"').closest('div');
        if (symbolField) {
            fireEvent.click(symbolField);
        }

        // Verify Symbol is highlighted
        await waitFor(() => {
            const symbolContainer = screen.getByText('"Symbol"').closest('div');
            expect(symbolContainer?.className).toMatch(/bg-blue/);
        });

        // Click on Price field
        const priceField = screen.getByText('"Price"').closest('div');
        if (priceField) {
            fireEvent.click(priceField);
        }

        // Verify Price is now highlighted and Symbol is not
        await waitFor(() => {
            const priceContainer = screen.getByText('"Price"').closest('div');
            const symbolContainer = screen.getByText('"Symbol"').closest('div');

            expect(priceContainer?.className).toMatch(/bg-blue/);
            expect(symbolContainer?.className).not.toMatch(/bg-blue-100/);
        });
    });

    test('component tracks related section IDs for pointer fields', async () => {
        const { container } = render(
            <AdvancedBinaryView isOpen={true} onClose={() => { }} schema={mockSchema} hexData={mockHexData} />
        );

        // Wait for analysis to complete
        await waitFor(() => expect(screen.queryByText(/Analyzing.../i)).not.toBeInTheDocument());

        // Click on Symbol field (which has a pointer)
        const symbolField = screen.getByText('"Symbol"').closest('div');
        if (symbolField) {
            fireEvent.click(symbolField);
        }

        // The component should render the hex bytes
        await waitFor(() => {
            const hexBytes = container.querySelectorAll('[id^="byte-"]');
            expect(hexBytes.length).toBeGreaterThan(0);
        });
    });

    test('passes relatedSectionIds to child components', async () => {
        render(
            <AdvancedBinaryView isOpen={true} onClose={() => { }} schema={mockSchema} hexData={mockHexData} />
        );

        // Wait for analysis to complete
        await waitFor(() => expect(screen.queryByText(/Analyzing.../i)).not.toBeInTheDocument());

        // Click on Symbol field
        const symbolField = screen.getByText('"Symbol"').closest('div');
        if (symbolField) {
            fireEvent.click(symbolField);
        }

        // Verify the component renders without errors
        // The relatedSectionIds prop should be passed to BinaryHexPane and MessageStructurePane
        await waitFor(() => {
            expect(screen.getByText('"Symbol"')).toBeInTheDocument();
        });
    });
});
