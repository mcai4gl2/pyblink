// Main App Component

import { useState } from 'react';
import { InputPanel } from './components/InputPanel';
import { OutputPanel } from './components/OutputPanel';
import { SchemaEditor } from './components/SchemaEditor';
import { convertMessage, validateSchema } from './services/api';
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

  const handleValidateSchema = async () => {
    console.log('Validating schema...');
    try {
      const response = await validateSchema({ schema });
      console.log('Validation response:', response);
      if (response.valid) {
        setSchemaError(undefined);
        setIsSchemaValid(true);
        setTimeout(() => setIsSchemaValid(false), 3000);
      } else {
        setSchemaError(response.error);
        setIsSchemaValid(false);
      }
    } catch (error) {
      console.error('Validation error:', error);
      setSchemaError('Failed to validate schema');
      setIsSchemaValid(false);
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
    } catch (error) {
      console.error('Convert error:', error);
      setResult({
        success: false,
        error: 'Failed to connect to API server. Make sure it is running on http://127.0.0.1:8000',
      });
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
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <h1 className="text-2xl font-bold text-gray-900">
            🔷 Blink Message Playground
          </h1>
          <p className="text-sm text-gray-600 mt-1">
            Convert Blink messages between all supported formats
          </p>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 h-[calc(100vh-180px)]">
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
      <footer className="max-w-7xl mx-auto px-4 py-4 text-center text-sm text-gray-600">
        <p>
          Backend API:{' '}
          <code className="px-2 py-1 bg-gray-200 rounded text-xs">
            {process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000'}
          </code>
        </p>
      </footer>
    </div>
  );
}

export default App;
