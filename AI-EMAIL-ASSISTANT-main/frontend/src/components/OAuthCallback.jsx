import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api, { gmail } from '../utils/api';

const OAuthCallback = () => {
  const [status, setStatus] = useState('processing');
  const [info, setInfo] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const st = params.get('status');
    const email = params.get('email');
    if (st === 'success') {
      setStatus('success');
      setInfo({ email });
      // Optionally refresh server-side session/account info
      // If user is authenticated, they can fetch /api/gmail/status
      try {
        gmail.status().then(resp => {
          // nothing required; component can show response
        }).catch(() => {});
      } catch (e) {}
      // After showing success for a short moment, navigate to /email
      setTimeout(() => navigate('/email'), 2200);
    } else {
      setStatus('failed');
      setTimeout(() => navigate('/email'), 2200);
    }
  }, [navigate]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        {status === 'processing' && <div>Processing OAuth response...</div>}
        {status === 'success' && (
          <div className="rounded-md bg-green-50 p-4">
            <div className="text-green-700">Connected Gmail account{info?.email ? `: ${info.email}` : ''}</div>
            <div className="text-sm text-gray-600 mt-2">Redirecting you back to the app...</div>
          </div>
        )}
        {status === 'failed' && (
          <div className="rounded-md bg-red-50 p-4">
            <div className="text-red-700">OAuth failed or was cancelled.</div>
            <div className="text-sm text-gray-600 mt-2">Returning to app...</div>
          </div>
        )}
      </div>
    </div>
  );
};

export default OAuthCallback;
