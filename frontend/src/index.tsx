import ReactDOM from 'react-dom/client';
import App from './App';
import ErrorBoundary from './components/ErrorBoundary';
import './index.css';
import reportWebVitals from './reportWebVitals';

// Disable React error overlay for ResizeObserver errors
if (process.env.NODE_ENV === 'development') {
  const originalError = console.error;
  console.error = (...args) => {
    if (
      typeof args[0] === 'string' &&
      args[0].includes('ResizeObserver loop')
    ) {
      return;
    }
    originalError.call(console, ...args);
  };
}

// Suppress ResizeObserver errors (harmless Monaco Editor warnings)
const suppressResizeObserver = () => {
  const resizeObserverErrHandler = window.onerror;
  window.onerror = (message, source, lineno, colno, error) => {
    if (message && message.toString().includes('ResizeObserver loop')) {
      return true;
    }
    if (resizeObserverErrHandler) {
      return resizeObserverErrHandler(message, source, lineno, colno, error);
    }
    return false;
  };
};

suppressResizeObserver();

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);
root.render(
  <ErrorBoundary>
    <App />
  </ErrorBoundary>
);

reportWebVitals();
