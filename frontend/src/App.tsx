// Main App Component

import { Save } from 'lucide-react';
import { useEffect, useState } from 'react';
import { InputPanel } from './components/InputPanel';
import { OutputPanel } from './components/OutputPanel';
import { SaveModal } from './components/SaveModal';
import { SchemaEditor } from './components/SchemaEditor';
import { ToastContainer, useToast } from './components/Toast';
import { EXAMPLES } from './data/examples';
import { convertMessage, loadPlayground, validateSchema } from './services/api';
import type { ConvertResponse, InputFormat } from './types';

// Example schema with nested classes and subclasses
const EXAMPLE_SCHEMA = `namespace Demo

# Base class for address information
Address/1 -> string Street, string City, u32 ZipCode

# Employee class with nested Address
Employee/2 -> string Name, u32 Age, Address HomeAddress

# Manager subclass extends Employee with additional fields
Manager/3 : Employee -> string Department, u32 TeamSize

# Company class with nested Manager
Company/4 -> string CompanyName, Manager CEO`;

// Example messages for each format
const EXAMPLE_MESSAGES: Record<InputFormat, string> = {
  json: `{"$type":"Demo:Company","CompanyName":"TechCorp","CEO":{"Name":"Alice","Age":45,"HomeAddress":{"Street":"123 Main St","City":"San Francisco","ZipCode":94102},"Department":"Engineering","TeamSize":50}}`,
  tag: `@Demo:Company|CompanyName=TechCorp|CEO={Name=Alice,Age=45,HomeAddress={Street=123 Main St,City=San Francisco,ZipCode=94102},Department=Engineering,TeamSize=50}`,
  xml: `<ns0:Company xmlns:ns0="Demo"><CompanyName>TechCorp</CompanyName><CEO /></ns0:Company>`,
  compact: `BB 84 88 54 65 63 68 43 6F 72 70 85 41 6C 69 63 65 AD 8B 31 32 33 20 4D 61 69 6E 20 53 74 8D 53 61 6E 20 46 72 61 6E 63 69 73 63 6F 16 5F 85 8B 45 6E 67 69 6E 65 65 72 69 6E 67 B2`,
  native: `70 00 00 00 04 00 00 00 00 00 00 00 00 00 00 00 20 00 00 00 28 00 00 00 2D 00 00 00 29 00 00 00 34 00 00 00 96 6F 01 00 3D 00 00 00 32 00 00 00 08 00 00 00 54 65 63 68 43 6F 72 70 05 00 00 00 41 6C 69 63 65 0B 00 00 00 31 32 33 20 4D 61 69 6E 20 53 74 0D 00 00 00 53 61 6E 20 46 72 61 6E 63 69 73 63 6F 0B 00 00 00 45 6E 67 69 6E 65 65 72 69 6E 67`,
};

function App() {
  const [schema, setSchema] = useState(EXAMPLE_SCHEMA);
  const [inputFormat, setInputFormat] = useState<InputFormat>('json');
  const [inputData, setInputData] = useState(EXAMPLE_MESSAGES.json);
  const [result, setResult] = useState<ConvertResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [schemaError, setSchemaError] = useState<string | undefined>();
  const [isSchemaValid, setIsSchemaValid] = useState(false);
  const [isSaveModalOpen, setIsSaveModalOpen] = useState(false);
  const [isLoadingPlayground, setIsLoadingPlayground] = useState(false);
  const [loadedPlaygroundTitle, setLoadedPlaygroundTitle] = useState<string | null>(null);

  // Toast notifications
  const { toasts, removeToast, showSuccess, showError, showInfo } = useToast();

  // Auto-save to localStorage (draft)
  useEffect(() => {
    const draft = { schema, inputFormat, inputData };
    localStorage.setItem('blink-playground-draft', JSON.stringify(draft));
  }, [schema, inputFormat, inputData]);

  // Load draft from localStorage on mount (if not loading from URL)
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const playgroundId = urlParams.get('p');

    if (!playgroundId) {
      const saved = localStorage.getItem('blink-playground-draft');
      if (saved) {
        try {
          const draft = JSON.parse(saved);
          // Only restore if it's different from the current default state
          const isDifferent = draft.schema !== schema ||
            draft.inputFormat !== inputFormat ||
            draft.inputData !== inputData;

          if (isDifferent && draft.schema) {
            setSchema(draft.schema);
            setInputFormat(draft.inputFormat || 'json');
            setInputData(draft.inputData || '');
            // Show toast after a brief delay to ensure toast system is ready
            setTimeout(() => showInfo('Draft restored from last session'), 100);
          }
        } catch (e) {
          console.error('Failed to load draft:', e);
        }
      }
    }
  }, []);

  // Load playground from URL parameter on mount
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const playgroundId = urlParams.get('p');

    if (playgroundId) {
      loadPlaygroundById(playgroundId);
    }
  }, []);

  const loadPlaygroundById = async (playgroundId: string) => {
    setIsLoadingPlayground(true);
    try {
      const response = await loadPlayground(playgroundId);

      if (response.success && response.playground) {
        const pg = response.playground;
        setSchema(pg.schema);
        setInputFormat(pg.input_format as InputFormat);
        setInputData(pg.input_data);
        setLoadedPlaygroundTitle(pg.title || null);

        showSuccess(`Loaded playground: ${pg.title || 'Untitled'}`);

        // Auto-convert after loading
        setTimeout(() => {
          handleConvert();
        }, 500);
      } else {
        console.error('Failed to load playground:', response.error);
        showError(`Failed to load playground: ${response.error || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Error loading playground:', error);
      showError('Failed to load playground. The link may be invalid or expired.');
    } finally {
      setIsLoadingPlayground(false);
    }
  };

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ctrl+Enter or Cmd+Enter: Convert
      if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        e.preventDefault();
        handleConvert();
      }

      // Ctrl+S or Cmd+S: Save
      if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault();
        setIsSaveModalOpen(true);
      }

      // Escape: Close modal
      if (e.key === 'Escape' && isSaveModalOpen) {
        setIsSaveModalOpen(false);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isSaveModalOpen]); // Re-bind when modal state changes

  const handleValidateSchema = async () => {
    console.log('Validating schema...');
    try {
      const response = await validateSchema({ schema });
      console.log('Validation response:', response);
      if (response.valid) {
        setSchemaError(undefined);
        setIsSchemaValid(true);
        showSuccess('Schema is valid!');
        setTimeout(() => setIsSchemaValid(false), 3000);
      } else {
        setSchemaError(response.error);
        setIsSchemaValid(false);
        showError('Schema validation failed');
      }
    } catch (error) {
      console.error('Validation error:', error);
      setSchemaError('Failed to validate schema');
      setIsSchemaValid(false);
      showError('Failed to validate schema');
    }
  };

  const handleConvert = async () => {
    setIsLoading(true);
    setSchemaError(undefined);
    console.log('Converting message...', { schema, inputFormat, inputData });

    try {
      const response = await convertMessage({
        schema,
        input_format: inputFormat,
        input_data: inputData,
      });
      console.log('Convert response:', response);

      setResult(response);
      if (response.success) {
        showSuccess('Message converted successfully!');
      } else {
        showError(`Conversion failed: ${response.error}`);
      }
    } catch (error) {
      console.error('Convert error:', error);
      setResult({
        success: false,
        error: 'Failed to connect to API server. Make sure it is running on http://127.0.0.1:8000',
      });
      showError('Failed to connect to API server');
    } finally {
      setIsLoading(false);
    }
  };

  const handleFormatChange = (format: InputFormat) => {
    setInputFormat(format);
    // Update input data with example for the new format
    setInputData(EXAMPLE_MESSAGES[format]);
  };

  return (
    <div className="min-h-screen bg-gray-100 flex flex-col">
      {/* Toast Notifications */}
      <ToastContainer toasts={toasts} onRemove={removeToast} />

      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                🔷 Blink Message Playground
                {loadedPlaygroundTitle && (
                  <span className="text-sm font-normal text-gray-600 ml-3">
                    ({loadedPlaygroundTitle})
                  </span>
                )}
              </h1>
              <p className="text-sm text-gray-600 mt-1">
                Convert Blink messages between all supported formats
              </p>
            </div>
            <div className="flex items-center gap-3">
              {/* Examples Dropdown */}
              <select
                onChange={(e) => {
                  const example = EXAMPLES.find(ex => ex.id === e.target.value);
                  if (example) {
                    setSchema(example.schema);
                    setInputFormat(example.inputFormat as InputFormat);
                    setInputData(example.inputData);
                    showInfo(`Loaded example: ${example.title}`);
                  }
                }}
                className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                defaultValue=""
              >
                <option value="" disabled>📚 Load Example...</option>
                {EXAMPLES.map(example => (
                  <option key={example.id} value={example.id}>
                    {example.title}
                  </option>
                ))}
              </select>

              <button
                onClick={() => setIsSaveModalOpen(true)}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors flex items-center gap-2 font-medium"
                disabled={isLoadingPlayground}
              >
                <Save className="w-4 h-4" />
                Save & Share
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Loading Indicator */}
      {isLoadingPlayground && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 shadow-xl">
            <p className="text-lg font-medium text-gray-800">Loading playground...</p>
          </div>
        </div>
      )}

      {/* Save Modal */}
      <SaveModal
        isOpen={isSaveModalOpen}
        onClose={() => setIsSaveModalOpen(false)}
        schema={schema}
        inputFormat={inputFormat}
        inputData={inputData}
      />

      {/* Main Content */}
      <main className="flex-1 max-w-7xl mx-auto px-4 py-6 w-full">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 min-h-[600px]">
          {/* Left Column: Schema + Input */}
          <div className="flex flex-col gap-6">
            {/* Schema Editor */}
            <div className="bg-white rounded-lg shadow-sm p-4 h-1/2">
              <SchemaEditor
                value={schema}
                onChange={setSchema}
                onValidate={handleValidateSchema}
                error={schemaError}
                isValid={isSchemaValid}
              />
            </div>

            {/* Input Panel */}
            <div className="bg-white rounded-lg shadow-sm p-4 h-1/2">
              <InputPanel
                format={inputFormat}
                value={inputData}
                onChange={setInputData}
                onFormatChange={handleFormatChange}
                onConvert={handleConvert}
                isLoading={isLoading}
              />
            </div>
          </div>

          {/* Right Column: Output */}
          <div className="bg-white rounded-lg shadow-sm">
            <div className="p-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-800">
                Output Formats
              </h2>
            </div>
            <div className="h-[calc(100%-60px)]">
              <OutputPanel result={result} />
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-gray-100 border-t border-gray-200 mt-auto">
        <div className="max-w-7xl mx-auto px-4 py-4 text-center text-sm text-gray-600">
          <p>
            Backend API:{' '}
            <code className="px-2 py-1 bg-gray-200 rounded text-xs">
              {process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000'}
            </code>
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;
