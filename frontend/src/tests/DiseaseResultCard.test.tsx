import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { DiseaseResultCard, DiseaseResult } from '../components/DiseaseResultCard';

// Mock AdvisoryCard
jest.mock('../components/AdvisoryCard', () => ({
  AdvisoryCard: () => <div data-testid="advisory-card">Advisory Recommendations</div>,
}));

// Mock AdvisoryService
jest.mock('../services/api', () => ({
  api: {
    get: jest.fn(() => Promise.resolve({ data: { success: true, data: {} } })),
    post: jest.fn(),
  },
}));

describe('DiseaseResultCard Component', () => {
  const mockResult: DiseaseResult = {
    report_id: 42,
    crop_type: 'Tomato',
    disease_predicted: 'Tomato Early Blight',
    confidence: 0.94,
    image_url: 'http://localhost/leaf.jpg',
    overlay_url: 'http://localhost/overlay.png',
    explanation: {
      visual_cues: 'Concentric target-board rings on lower foliage.',
    },
  };

  const mockOnRequestValidation = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders diagnosis results and confidence accurately', () => {
    render(
      <DiseaseResultCard
        result={mockResult}
        onRequestValidation={mockOnRequestValidation}
      />
    );

    expect(screen.getByText('Tomato Early Blight')).toBeInTheDocument();
    expect(screen.getByText(/Tomato Diagnosis/i)).toBeInTheDocument();
    expect(screen.getByText('94%')).toBeInTheDocument();
    expect(screen.getByText(/Concentric target-board rings/i)).toBeInTheDocument();
  });

  it('toggles Grad-CAM explainability overlay correctly', () => {
    render(
      <DiseaseResultCard
        result={mockResult}
        onRequestValidation={mockOnRequestValidation}
      />
    );

    const toggleBtn = screen.getByRole('button', { name: /Overlay: ON/i });
    expect(toggleBtn).toBeInTheDocument();

    fireEvent.click(toggleBtn);
    expect(screen.getByRole('button', { name: /Overlay: OFF/i })).toBeInTheDocument();
  });

  it('calls onRequestValidation when expert review button is clicked', () => {
    render(
      <DiseaseResultCard
        result={mockResult}
        onRequestValidation={mockOnRequestValidation}
      />
    );

    const reviewBtn = screen.getByRole('button', { name: /Request Expert Review/i });
    fireEvent.click(reviewBtn);

    expect(mockOnRequestValidation).toHaveBeenCalledWith(42);
  });
});
