import React, { useEffect, useState } from 'react';
import { models } from '../utils/api';
import { toast } from 'react-toastify';

const ModelRegistry = () => {
  const [modelList, setModelList] = useState([]);
  const [samples, setSamples] = useState([{ text: '', label: '' }]);
  const [retraining, setRetraining] = useState(false);

  const loadModels = async () => {
    try {
      const resp = await models.list();
      setModelList(resp.data.models || []);
    } catch (err) {
      toast.error('Failed to load models');
    }
  };

  useEffect(() => {
    loadModels();
  }, []);

  const addSample = () => setSamples(prev => [...prev, { text: '', label: '' }]);
  const removeSample = (idx) => setSamples(prev => prev.filter((_, i) => i !== idx));
  const updateSample = (idx, field, value) => setSamples(prev => prev.map((s, i) => i === idx ? { ...s, [field]: value } : s));

  const handleRetrain = async () => {
    const payload = samples.filter(s => s.text.trim() && s.label.trim());
    if (payload.length === 0) {
      toast.error('Add at least one labeled sample');
      return;
    }
    setRetraining(true);
    try {
      const resp = await models.retrain(payload);
      if (resp.data.retrained) {
        toast.success('Retrain started / completed');
        setSamples([{ text: '', label: '' }]);
        await loadModels();
      } else {
        toast.error('Retrain did not succeed');
      }
    } catch (err) {
      toast.error('Retrain failed');
    } finally {
      setRetraining(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="bg-white shadow sm:rounded-lg p-6">
        <h2 className="text-lg font-medium">Model Registry</h2>
        <p className="text-sm text-gray-600">View persisted intent models and retrain the classifier.</p>

        <div className="mt-4">
          <h3 className="font-medium">Available Models</h3>
          <div className="mt-2 overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead>
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Created</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Samples</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Accuracy</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Path</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {modelList.map((m) => (
                  <tr key={m._id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{m.created_at ? new Date(m.created_at * 1000).toLocaleString() : 'n/a'}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{m.sample_count || '-'}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{m.accuracy ? (m.accuracy).toFixed(2) : '-'}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{m.path || '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="mt-6">
          <h3 className="font-medium">Retrain Intent Classifier</h3>
          <p className="text-sm text-gray-500">Provide labeled samples (text + label) to retrain the intent classifier.</p>
          <div className="mt-3 space-y-3">
            {samples.map((s, idx) => (
              <div key={idx} className="flex space-x-2">
                <input value={s.text} onChange={(e) => updateSample(idx, 'text', e.target.value)} placeholder="Text example" className="flex-1 border px-2 py-1 rounded" />
                <input value={s.label} onChange={(e) => updateSample(idx, 'label', e.target.value)} placeholder="Label" className="w-40 border px-2 py-1 rounded" />
                <button type="button" onClick={() => removeSample(idx)} className="text-red-600">Remove</button>
              </div>
            ))}
            <div className="flex space-x-2">
              <button onClick={addSample} className="px-3 py-1 bg-gray-100 rounded">Add sample</button>
              <button onClick={handleRetrain} disabled={retraining} className="px-3 py-1 bg-indigo-600 text-white rounded">{retraining ? 'Retraining...' : 'Retrain'}</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ModelRegistry;
