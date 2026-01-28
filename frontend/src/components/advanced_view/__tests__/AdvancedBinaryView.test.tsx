import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import * as api from '../../../services/api';
import { AdvancedBinaryView } from '../AdvancedBinaryView';

// Mock API
jest.mock('../../../services/api');

const mockAnalyzeBinary = api.analyzeBinary as jest.Mock;
const mockConvertMessage = api.convertMessage as jest.Mock;

const mockAnalysisResponse = {
    success: true,
    sections: [
        { id: 's1', startOffset: 0, endOffset: 4, label: 'Size', type: 'header', color: 'blue', rawValue: '04000000', interpretedValue: '4' },
        { id: 's2', startOffset: 4, endOffset: 8, label: 'Data', type: 'data', color: 'green', rawValue: 'DEADBEEF', interpretedValue: 'Data' }
    ],
    fields: [],
    root_type: 'Demo:Msg'
};

const mockHexData = "04000000DEADBEEF";
const mockSchema = "schema definition";

describe('AdvancedBinaryView Integration', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        mockAnalyzeBinary.mockResolvedValue(mockAnalysisResponse);
    });

    test('renders correctly and fetches analysis data', async () => {
        render(<AdvancedBinaryView isOpen={true} onClose={() => { }} schema={mockSchema} hexData={mockHexData} />);

        // Header
        expect(screen.getByText(/Advanced Binary Inspector/i)).toBeInTheDocument();

        // Loading state
        expect(screen.getByText(/Analyzing.../i)).toBeInTheDocument();

        // API Call
        await waitFor(() => {
            expect(mockAnalyzeBinary).toHaveBeenCalledWith({
                schema: mockSchema,
                binary_hex: "04000000DEADBEEF"
            });
        });

        // Data loaded
        await waitFor(() => {
            expect(screen.queryByText(/Analyzing.../i)).not.toBeInTheDocument();
        });
    });

    test('toggles search bar and counts matches', async () => {
        render(<AdvancedBinaryView isOpen={true} onClose={() => { }} schema={mockSchema} hexData={mockHexData} />);

        await waitFor(() => expect(screen.queryByText(/Analyzing.../i)).not.toBeInTheDocument());

        // Click Search Toggle
        const toggleBtn = screen.getByTitle(/Toggle Search/i);
        fireEvent.click(toggleBtn);

        const input = screen.getByPlaceholderText(/Search text.../i);
        expect(input).toBeInTheDocument();

        // Switch to Hex Search - Use Title!
        const hexToggle = screen.getByTitle('Toggle Hex Search');
        fireEvent.click(hexToggle);

        expect(screen.getByPlaceholderText(/Search hex/i)).toBeInTheDocument();

        // Type hex
        fireEvent.change(input, { target: { value: 'DEAD' } });

        // Match 1/1
        await waitFor(() => {
            expect(screen.getByText('1/1')).toBeInTheDocument();
        });
    });

    test('opens Diff Modal and handles JSON input', async () => {
        render(<AdvancedBinaryView isOpen={true} onClose={() => { }} schema={mockSchema} hexData={mockHexData} />);

        await waitFor(() => expect(screen.queryByText(/Analyzing.../i)).not.toBeInTheDocument());

        // Click Diff Button
        const diffBtn = screen.getByTitle(/Diff \/ Compare Mode/i);
        fireEvent.click(diffBtn);

        expect(screen.getByText(/Compare Binary Data/i)).toBeInTheDocument();

        // Switch to JSON
        const jsonTab = screen.getByText(/JSON Input/i);
        fireEvent.click(jsonTab);

        // Type JSON
        const textarea = screen.getByLabelText(/Paste JSON Object:/i);
        fireEvent.change(textarea, { target: { value: '{ "test": 1 }' } });

        expect(screen.getByText(/Demo:Msg/i)).toBeInTheDocument();

        mockConvertMessage.mockResolvedValue({
            success: true,
            outputs: {
                native_binary: { rawHex: "04000000CAFEBABE" }
            }
        });

        const compareBtn = screen.getByText('Compare');
        fireEvent.click(compareBtn);

        // Wait for Diff Mode
        await waitFor(() => {
            expect(screen.getByText('Original')).toBeInTheDocument();
        });

        expect(screen.getByText(/\d+ Differences/i)).toBeInTheDocument();
    });
});
