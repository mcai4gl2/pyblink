import React from 'react';
import { render, screen } from '@testing-library/react';
import App from './App';

test('renders Blink Message Playground header', () => {
  render(<App />);
  const headerElement = screen.getByText(/Blink Message Playground/i);
  expect(headerElement).toBeInTheDocument();
});
