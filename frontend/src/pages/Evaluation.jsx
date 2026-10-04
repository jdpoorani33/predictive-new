import React from 'react';
import ModelEvaluation from '../components/ModelEvaluation';

const Evaluation = ({
  plcsList,
  selectedPlc,
  setSelectedPlc,
  selectedTag,
  setSelectedTag,
  modelData
}) => {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between pb-2 border-b border-gray-200">
        <div>
          <h1 className="text-base font-bold text-gray-900">Random Forest Model Diagnostics & Evaluation</h1>
          <p className="text-xs text-gray-500">Per-PLC ground-truth performance evaluation & multi-domain anomaly classification diagnostics</p>
        </div>
        {modelData?.isFallback && (
          <span className="px-2.5 py-1 text-xs font-semibold text-amber-800 bg-amber-100 border border-amber-300 rounded-md">
            Baseline Metrics Active
          </span>
        )}
      </div>
      <ModelEvaluation
        plcsList={plcsList}
        selectedPlc={selectedPlc}
        setSelectedPlc={setSelectedPlc}
        selectedTag={selectedTag}
        setSelectedTag={setSelectedTag}
        modelData={modelData}
      />
    </div>
  );
};

export default Evaluation;
