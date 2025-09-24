import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { 
  PaperAirplaneIcon, 
  SparklesIcon,
  DocumentDuplicateIcon,
  DocumentArrowDownIcon,
  ArrowPathIcon,
  ClipboardIcon,
  PaperClipIcon,
  ExclamationCircleIcon,
} from '@heroicons/react/24/solid';
import { toast } from 'react-toastify';

const TONE_OPTIONS = [
  { value: 'Formal', description: 'Professional and business-like' },
  { value: 'Friendly', description: 'Warm and conversational' },
  { value: 'Persuasive', description: 'Convincing and impactful' },
  { value: 'Apologetic', description: 'Sincere and regretful' },
  { value: 'Assertive', description: 'Direct and confident' }
];

const MAX_CONTEXT_LENGTH = 2000;
const MAX_ATTACHMENTS = 5;
const ALLOWED_FILE_TYPES = ['application/pdf', 'image/jpeg', 'image/png', 'application/msword'];
const MAX_FILE_SIZE = 5 * 1024 * 1024; // 5MB

const EmailForm = () => {
  const [formData, setFormData] = useState({
    recipient: '',
    cc: '',
    bcc: '',
    subject: '',
    context: '',
    tone: 'Formal'
  });

  const [attachments, setAttachments] = useState([]);
  const [generatedEmail, setGeneratedEmail] = useState('');
  const [emailHistory, setEmailHistory] = useState([]);
  const [currentVersion, setCurrentVersion] = useState(0);
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(false);
  const [errors, setErrors] = useState({});
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [wordCount, setWordCount] = useState(0);
  const fileInputRef = useRef(null);
  const emailTextAreaRef = useRef(null);
  const contextTextAreaRef = useRef(null);

  useEffect(() => {
    // Update word count
    setWordCount(formData.context.trim().split(/\s+/).length);
    
    // Auto-resize textareas
    autoResizeTextArea(contextTextAreaRef.current);
    if (emailTextAreaRef.current) {
      autoResizeTextArea(emailTextAreaRef.current);
    }
  }, [formData.context, generatedEmail]);

  const autoResizeTextArea = (element) => {
    if (element) {
      element.style.height = 'auto';
      element.style.height = `${element.scrollHeight}px`;
    }
  };

  const validateEmail = (email) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  const validateEmails = (emails) => {
    if (!emails) return true;
    return emails.split(',').every(email => validateEmail(email.trim()));
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    
    // Clear errors for the field being edited
    setErrors(prev => ({
      ...prev,
      [name]: undefined
    }));
  };

  const handleFileChange = (e) => {
    const files = Array.from(e.target.files);
    const newErrors = {};
    
    // Validate files
    const validFiles = files.filter(file => {
      if (!ALLOWED_FILE_TYPES.includes(file.type)) {
        newErrors.attachments = 'Invalid file type';
        return false;
      }
      if (file.size > MAX_FILE_SIZE) {
        newErrors.attachments = 'File too large (max 5MB)';
        return false;
      }
      return true;
    });

    if (attachments.length + validFiles.length > MAX_ATTACHMENTS) {
      newErrors.attachments = `Maximum ${MAX_ATTACHMENTS} files allowed`;
      setErrors(prev => ({ ...prev, ...newErrors }));
      return;
    }

    setAttachments(prev => [...prev, ...validFiles]);
    setErrors(prev => ({ ...prev, attachments: undefined }));
  };

  const removeAttachment = (index) => {
    setAttachments(prev => prev.filter((_, i) => i !== index));
  };

  const validateForm = () => {
    const newErrors = {};

    if (!formData.subject.trim()) {
      newErrors.subject = 'Subject is required';
    }
    if (!formData.context.trim()) {
      newErrors.context = 'Context is required';
    }
    if (formData.context.length > MAX_CONTEXT_LENGTH) {
      newErrors.context = 'Context is too long';
    }
    if (formData.cc && !validateEmails(formData.cc)) {
      newErrors.cc = 'Invalid CC email address(es)';
    }
    if (formData.bcc && !validateEmails(formData.bcc)) {
      newErrors.bcc = 'Invalid BCC email address(es)';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleGenerate = async (e) => {
    e.preventDefault();
    if (!validateForm()) return;

    setLoading(true);
    try {
      const response = await axios.post('/api/email/generate', {
        subject: formData.subject,
        context: formData.context,
        tone: formData.tone,
        cc: formData.cc,
        bcc: formData.bcc
      });

      const newEmail = response.data.body;
      setGeneratedEmail(newEmail);
      setEmailHistory(prev => [...prev, newEmail]);
      setCurrentVersion(prev => prev + 1);
      toast.success('Email generated successfully!');
    } catch (error) {
      toast.error(error.response?.data?.error || 'Failed to generate email');
    } finally {
      setLoading(false);
    }
  };

  const handleRegenerateEmail = async () => {
    await handleGenerate({ preventDefault: () => {} });
  };

  const handleSend = async () => {
    if (!validateForm()) return;
    if (!formData.recipient || !validateEmail(formData.recipient)) {
      setErrors(prev => ({ ...prev, recipient: 'Valid recipient email required' }));
      return;
    }
    if (!generatedEmail) {
      toast.error('Please generate email content first');
      return;
    }

    setSending(true);
    try {
      const formDataToSend = new FormData();
      formDataToSend.append('recipient', formData.recipient);
      formDataToSend.append('subject', formData.subject);
      formDataToSend.append('body', generatedEmail);
      if (formData.cc) formDataToSend.append('cc', formData.cc);
      if (formData.bcc) formDataToSend.append('bcc', formData.bcc);
      attachments.forEach(file => formDataToSend.append('attachments', file));

      await axios.post('/api/email/send', formDataToSend, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      toast.success('Email sent successfully!');
      // Reset form
      setFormData({
        recipient: '',
        cc: '',
        bcc: '',
        subject: '',
        context: '',
        tone: 'Formal'
      });
      setGeneratedEmail('');
      setAttachments([]);
      setEmailHistory([]);
      setCurrentVersion(0);
    } catch (error) {
      toast.error(error.response?.data?.error || 'Failed to send email');
    } finally {
      setSending(false);
    }
  };

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(generatedEmail);
      toast.success('Copied to clipboard!');
    } catch (error) {
      toast.error('Failed to copy to clipboard');
    }
  };

  const downloadEmail = () => {
    const element = document.createElement('a');
    const file = new Blob([generatedEmail], { type: 'text/plain' });
    element.href = URL.createObjectURL(file);
    element.download = `email_${formData.subject.replace(/[^a-z0-9]/gi, '_').toLowerCase()}.txt`;
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  const undoVersion = () => {
    if (currentVersion > 0) {
      setCurrentVersion(prev => prev - 1);
      setGeneratedEmail(emailHistory[currentVersion - 1]);
    }
  };

  const redoVersion = () => {
    if (currentVersion < emailHistory.length - 1) {
      setCurrentVersion(prev => prev + 1);
      setGeneratedEmail(emailHistory[currentVersion + 1]);
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="bg-white shadow sm:rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-gray-900">
            Generate Professional Email
          </h3>
          
          <form onSubmit={handleGenerate} className="mt-5 space-y-6">
            <div className="grid grid-cols-1 gap-6">
              {/* Basic Fields */}
              <div>
                <label htmlFor="recipient" className="block text-sm font-medium text-gray-700">
                  To
                </label>
                <input
                  type="email"
                  name="recipient"
                  id="recipient"
                  value={formData.recipient}
                  onChange={handleChange}
                  className={`mt-1 block w-full shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm border-gray-300 rounded-md ${
                    errors.recipient ? 'border-red-500' : ''
                  }`}
                  placeholder="recipient@example.com"
                />
                {errors.recipient && (
                  <p className="mt-1 text-sm text-red-500">{errors.recipient}</p>
                )}
              </div>

              {/* Advanced Options Toggle */}
              <div className="flex items-center">
                <button
                  type="button"
                  onClick={() => setShowAdvanced(!showAdvanced)}
                  className="text-sm text-indigo-600 hover:text-indigo-800"
                >
                  {showAdvanced ? 'Hide Advanced Options' : 'Show Advanced Options'}
                </button>
              </div>

              {/* Advanced Fields */}
              {showAdvanced && (
                <>
                  <div>
                    <label htmlFor="cc" className="block text-sm font-medium text-gray-700">
                      CC
                    </label>
                    <input
                      type="text"
                      name="cc"
                      id="cc"
                      value={formData.cc}
                      onChange={handleChange}
                      className={`mt-1 block w-full shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm border-gray-300 rounded-md ${
                        errors.cc ? 'border-red-500' : ''
                      }`}
                      placeholder="cc1@example.com, cc2@example.com"
                    />
                    {errors.cc && (
                      <p className="mt-1 text-sm text-red-500">{errors.cc}</p>
                    )}
                  </div>

                  <div>
                    <label htmlFor="bcc" className="block text-sm font-medium text-gray-700">
                      BCC
                    </label>
                    <input
                      type="text"
                      name="bcc"
                      id="bcc"
                      value={formData.bcc}
                      onChange={handleChange}
                      className={`mt-1 block w-full shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm border-gray-300 rounded-md ${
                        errors.bcc ? 'border-red-500' : ''
                      }`}
                      placeholder="bcc1@example.com, bcc2@example.com"
                    />
                    {errors.bcc && (
                      <p className="mt-1 text-sm text-red-500">{errors.bcc}</p>
                    )}
                  </div>
                </>
              )}

              <div>
                <label htmlFor="subject" className="block text-sm font-medium text-gray-700">
                  Subject
                </label>
                <input
                  type="text"
                  name="subject"
                  id="subject"
                  required
                  value={formData.subject}
                  onChange={handleChange}
                  className={`mt-1 block w-full shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm border-gray-300 rounded-md ${
                    errors.subject ? 'border-red-500' : ''
                  }`}
                  placeholder="Enter email subject"
                />
                {errors.subject && (
                  <p className="mt-1 text-sm text-red-500">{errors.subject}</p>
                )}
              </div>

              <div>
                <label htmlFor="tone" className="block text-sm font-medium text-gray-700">
                  Tone
                </label>
                <select
                  name="tone"
                  id="tone"
                  value={formData.tone}
                  onChange={handleChange}
                  className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
                >
                  {TONE_OPTIONS.map(({ value, description }) => (
                    <option key={value} value={value} title={description}>
                      {value}
                    </option>
                  ))}
                </select>
                <p className="mt-1 text-sm text-gray-500">
                  {TONE_OPTIONS.find(t => t.value === formData.tone)?.description}
                </p>
              </div>

              <div>
                <label htmlFor="context" className="block text-sm font-medium text-gray-700">
                  Context or Details
                </label>
                <textarea
                  ref={contextTextAreaRef}
                  name="context"
                  id="context"
                  required
                  rows={4}
                  value={formData.context}
                  onChange={handleChange}
                  className={`mt-1 block w-full shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm border-gray-300 rounded-md ${
                    errors.context ? 'border-red-500' : ''
                  }`}
                  placeholder="Enter the context or details for your email..."
                />
                <div className="mt-1 flex justify-between text-sm">
                  <span className={`${wordCount > MAX_CONTEXT_LENGTH ? 'text-red-500' : 'text-gray-500'}`}>
                    {wordCount} words
                  </span>
                  {errors.context && (
                    <span className="text-red-500">{errors.context}</span>
                  )}
                </div>
              </div>

              {/* File Attachments */}
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Attachments
                </label>
                <div className="mt-1 flex items-center">
                  <button
                    type="button"
                    onClick={() => fileInputRef.current?.click()}
                    className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                  >
                    <PaperClipIcon className="h-5 w-5 mr-2" />
                    Attach Files
                  </button>
                  <input
                    type="file"
                    ref={fileInputRef}
                    onChange={handleFileChange}
                    multiple
                    accept=".pdf,.doc,.docx,.jpg,.jpeg,.png"
                    className="hidden"
                  />
                  <span className="ml-3 text-sm text-gray-500">
                    {attachments.length} / {MAX_ATTACHMENTS} files
                  </span>
                </div>
                {errors.attachments && (
                  <p className="mt-1 text-sm text-red-500">{errors.attachments}</p>
                )}
                {attachments.length > 0 && (
                  <ul className="mt-2 divide-y divide-gray-200">
                    {attachments.map((file, index) => (
                      <li key={index} className="py-2 flex justify-between items-center">
                        <span className="text-sm text-gray-700">{file.name}</span>
                        <button
                          type="button"
                          onClick={() => removeAttachment(index)}
                          className="text-red-600 hover:text-red-800"
                        >
                          Remove
                        </button>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex justify-end space-x-4">
              <button
                type="submit"
                disabled={loading}
                className={`inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 ${
                  loading ? 'opacity-50 cursor-not-allowed' : ''
                }`}
              >
                <SparklesIcon className="h-5 w-5 mr-2" />
                {loading ? 'Generating...' : 'Generate Email'}
              </button>
            </div>
          </form>

          {/* Generated Email Section */}
          {generatedEmail && (
            <div className="mt-6">
              <div className="flex justify-between items-center mb-2">
                <label className="block text-sm font-medium text-gray-700">
                  Generated Email
                </label>
                <div className="flex space-x-2">
                  <button
                    type="button"
                    onClick={undoVersion}
                    disabled={currentVersion === 0}
                    className="text-gray-500 hover:text-gray-700 disabled:opacity-50"
                    title="Undo"
                  >
                    Undo
                  </button>
                  <button
                    type="button"
                    onClick={redoVersion}
                    disabled={currentVersion === emailHistory.length - 1}
                    className="text-gray-500 hover:text-gray-700 disabled:opacity-50"
                    title="Redo"
                  >
                    Redo
                  </button>
                  <button
                    type="button"
                    onClick={handleRegenerateEmail}
                    className="text-gray-500 hover:text-gray-700"
                    title="Regenerate"
                  >
                    <ArrowPathIcon className="h-5 w-5" />
                  </button>
                  <button
                    type="button"
                    onClick={copyToClipboard}
                    className="text-gray-500 hover:text-gray-700"
                    title="Copy to clipboard"
                  >
                    <ClipboardIcon className="h-5 w-5" />
                  </button>
                  <button
                    type="button"
                    onClick={downloadEmail}
                    className="text-gray-500 hover:text-gray-700"
                    title="Download as text"
                  >
                    <DocumentArrowDownIcon className="h-5 w-5" />
                  </button>
                </div>
              </div>
              <div className="mt-1 relative">
                <textarea
                  ref={emailTextAreaRef}
                  rows={8}
                  value={generatedEmail}
                  onChange={(e) => setGeneratedEmail(e.target.value)}
                  className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                />
                <div className="absolute bottom-2 right-2 flex space-x-2">
                  <span className="text-sm text-gray-500">
                    Version {currentVersion + 1} of {emailHistory.length}
                  </span>
                </div>
              </div>
              
              {/* Send Button */}
              <div className="mt-4 flex justify-end space-x-4">
                <button
                  type="button"
                  onClick={handleSend}
                  disabled={sending}
                  className={`inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md shadow-sm text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 ${
                    sending ? 'opacity-50 cursor-not-allowed' : ''
                  }`}
                >
                  <PaperAirplaneIcon className="h-5 w-5 mr-2" />
                  {sending ? 'Sending...' : 'Send Email'}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default EmailForm;
