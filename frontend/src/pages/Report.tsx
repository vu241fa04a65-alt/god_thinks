import React, { useState } from 'react';
import { UploadForm } from '../components/UploadForm';
import { DiseaseResultCard, DiseaseResult } from '../components/DiseaseResultCard';
import { ExpertService } from '../services/api';

export const Report: React.FC = () => {
  const [result, setResult] = useState<DiseaseResult | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  const handleDiagnosisComplete = (diagnosisResult: DiseaseResult) => {
    setResult(diagnosisResult);
    window.scrollTo({ top: 400, behavior: 'smooth' });
  };

  const handleRequestValidation = async (reportId: number) => {
    try {
      // In a real scenario, this alerts local experts or changes status
      setStatusMessage(`Validation request dispatched for Report #${reportId}. Our agronomists will review.`);
      setTimeout(() => setStatusMessage(null), 5000);
    } catch (err) {
      // Handle error
    }
  };

  return (
    <div className="max-w-5xl mx-auto px-4 py-8 space-y-8">
      <div>
        <h1 className="text-3xl font-extrabold text-gray-900 tracking-tight">Crop Disease Diagnosis</h1>
        <p className="text-sm text-gray-600 mt-1">
          Submit leaf photos to receive instantaneous AI disease predictions, Grad-CAM visual heatmaps, and treatment advice.
        </p>
      </div>

      {statusMessage && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl text-emerald-800 text-sm font-medium">
          {statusMessage}
        </div>
      )}

      {/* Upload Component */}
      <UploadForm onDiagnosisComplete={handleDiagnosisComplete} />

      {/* Display Result Card when available */}
      {result && (
        <div className="pt-4">
          <DiseaseResultCard
            result={result}
            onRequestValidation={handleRequestValidation}
          />
        </div>
      )}
    </div>
  );
};
