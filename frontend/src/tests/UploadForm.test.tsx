import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { UploadForm } from '../components/UploadForm';
import { AuthProvider } from '../context/AuthContext';
import { ToastProvider } from '../context/ToastContext';

// Mock ReportService and OfflineSyncService and api
jest.mock('../services/api', () => ({
  api: {
    post: jest.fn(() => Promise.resolve({ data: { success: true, data: {} } })),
    get: jest.fn(() => Promise.resolve({ data: { success: true, data: {} } })),
  },
  getAccessToken: jest.fn(() => null),
  setTokens: jest.fn(),
  clearTokens: jest.fn(),
  ReportService: {
    uploadReport: jest.fn(() =>
      Promise.resolve({
        data: {
          success: true,
          data: {
            report_id: 123,
            crop_type: 'Tomato',
            disease_predicted: 'Tomato Early Blight',
            confidence: 0.94,
            image_url: 'http://localhost/sample.jpg',
            points_awarded: 10,
          },
        },
      })
    ),
  },
}));

jest.mock('../services/offlineSync', () => ({
  OfflineSyncService: {
    saveReportLocally: jest.fn(),
    getOfflineReports: jest.fn(() => Promise.resolve([])),
  },
}));

const renderWithProviders = (ui: React.ReactElement) => {
  return render(
    <AuthProvider>
      <ToastProvider>{ui}</ToastProvider>
    </AuthProvider>
  );
};

describe('UploadForm Component', () => {
  const mockOnDiagnosisComplete = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders crop selector and upload dropzone correctly', () => {
    renderWithProviders(<UploadForm onDiagnosisComplete={mockOnDiagnosisComplete} />);

    expect(screen.getByText(/Crop Variety/i)).toBeInTheDocument();
    expect(screen.getByText(/Field Location/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Analyze Crop Health/i })).toBeInTheDocument();
  });

  it('disables submit button when no file is selected', () => {
    renderWithProviders(<UploadForm onDiagnosisComplete={mockOnDiagnosisComplete} />);

    const submitBtn = screen.getByRole('button', { name: /Analyze Crop Health/i });
    expect(submitBtn).toBeDisabled();
  });

  it('updates crop type when selection changes', () => {
    renderWithProviders(<UploadForm onDiagnosisComplete={mockOnDiagnosisComplete} />);

    const select = screen.getByRole('combobox');
    fireEvent.change(select, { target: { value: 'Potato' } });
    expect(select).toHaveValue('Potato');
  });

  it('accepts file upload and enables submission button', async () => {
    renderWithProviders(<UploadForm onDiagnosisComplete={mockOnDiagnosisComplete} />);

    const file = new File(['dummy-content'], 'leaf.jpg', { type: 'image/jpeg' });
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;

    expect(input).toBeInTheDocument();
    fireEvent.change(input, { target: { files: [file] } });

    await waitFor(() => {
      const submitBtn = screen.getByRole('button', { name: /Analyze Crop Health/i });
      expect(submitBtn).not.toBeDisabled();
    });
  });
});
