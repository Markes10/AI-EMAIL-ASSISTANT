import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { format } from 'date-fns';
import {
  DocumentTextIcon,
  ArrowDownTrayIcon,
  FunnelIcon,
  CalendarIcon,
  EnvelopeIcon,
} from '@heroicons/react/24/outline';
import { toast } from 'react-toastify';

const HistoryViewer = () => {
  const [emails, setEmails] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState({
    searchTerm: '',
    tone: '',
    dateRange: 'all'
  });
  const [sortConfig, setSortConfig] = useState({
    key: 'timestamp',
    direction: 'desc'
  });
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    fetchEmails();
  }, []);

  const fetchEmails = async () => {
    try {
      const response = await axios.get('/api/history');
      setEmails(response.data);
    } catch (error) {
      toast.error('Failed to fetch email history');
    } finally {
      setLoading(false);
    }
  };

  const handleExportPDF = async (emailId) => {
    setExporting(true);
    try {
      const response = await axios.get(`/api/history/export/${emailId}`, {
        responseType: 'blob'
      });
      
      // Create blob link to download
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `email_${emailId}.pdf`);
      
      // Append to html link element page
      document.body.appendChild(link);
      
      // Start download
      link.click();
      
      // Clean up and remove the link
      link.parentNode.removeChild(link);
      toast.success('PDF exported successfully');
    } catch (error) {
      toast.error('Failed to export PDF');
    } finally {
      setExporting(false);
    }
  };

  const handleSort = (key) => {
    setSortConfig(current => ({
      key,
      direction: current.key === key && current.direction === 'asc' ? 'desc' : 'asc'
    }));
  };

  const handleFilterChange = (e) => {
    const { name, value } = e.target;
    setFilter(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const filteredAndSortedEmails = () => {
    let filtered = [...emails];

    // Apply filters
    if (filter.searchTerm) {
      filtered = filtered.filter(email =>
        email.subject.toLowerCase().includes(filter.searchTerm.toLowerCase()) ||
        email.body.toLowerCase().includes(filter.searchTerm.toLowerCase())
      );
    }

    if (filter.tone) {
      filtered = filtered.filter(email =>
        email.tone.toLowerCase() === filter.tone.toLowerCase()
      );
    }

    if (filter.dateRange !== 'all') {
      const now = new Date();
      const cutoff = new Date();
      switch (filter.dateRange) {
        case 'week':
          cutoff.setDate(now.getDate() - 7);
          break;
        case 'month':
          cutoff.setMonth(now.getMonth() - 1);
          break;
        case 'year':
          cutoff.setFullYear(now.getFullYear() - 1);
          break;
        default:
          break;
      }
      filtered = filtered.filter(email =>
        new Date(email.timestamp) >= cutoff
      );
    }

    // Apply sorting
    filtered.sort((a, b) => {
      let comparison = 0;
      switch (sortConfig.key) {
        case 'timestamp':
          comparison = new Date(a.timestamp) - new Date(b.timestamp);
          break;
        case 'subject':
          comparison = a.subject.localeCompare(b.subject);
          break;
        case 'tone':
          comparison = a.tone.localeCompare(b.tone);
          break;
        default:
          break;
      }
      return sortConfig.direction === 'asc' ? comparison : -comparison;
    });

    return filtered;
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-indigo-500"></div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Filters */}
      <div className="bg-white shadow rounded-lg mb-6 p-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Search
            </label>
            <div className="relative">
              <input
                type="text"
                name="searchTerm"
                value={filter.searchTerm}
                onChange={handleFilterChange}
                placeholder="Search emails..."
                className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
              />
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <FunnelIcon className="h-5 w-5 text-gray-400" />
              </div>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Tone
            </label>
            <select
              name="tone"
              value={filter.tone}
              onChange={handleFilterChange}
              className="block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
            >
              <option value="">All Tones</option>
              <option value="formal">Formal</option>
              <option value="friendly">Friendly</option>
              <option value="persuasive">Persuasive</option>
              <option value="apologetic">Apologetic</option>
              <option value="assertive">Assertive</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Date Range
            </label>
            <select
              name="dateRange"
              value={filter.dateRange}
              onChange={handleFilterChange}
              className="block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
            >
              <option value="all">All Time</option>
              <option value="week">Past Week</option>
              <option value="month">Past Month</option>
              <option value="year">Past Year</option>
            </select>
          </div>
        </div>
      </div>

      {/* Email List */}
      <div className="bg-white shadow overflow-hidden sm:rounded-lg">
        <div className="divide-y divide-gray-200">
          {filteredAndSortedEmails().map((email) => (
            <div key={email.id} className="p-4 hover:bg-gray-50">
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <div className="flex items-center">
                    <EnvelopeIcon className="h-5 w-5 text-gray-400 mr-2" />
                    <h3 className="text-lg font-medium text-gray-900">
                      {email.subject}
                    </h3>
                  </div>
                  <div className="mt-2 text-sm text-gray-500 line-clamp-2">
                    {email.body}
                  </div>
                  <div className="mt-2 flex items-center text-sm text-gray-500">
                    <CalendarIcon className="h-4 w-4 mr-1" />
                    {format(new Date(email.timestamp), 'PPp')}
                    <span className="ml-4 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-indigo-100 text-indigo-800">
                      {email.tone}
                    </span>
                  </div>
                </div>
                <button
                  onClick={() => handleExportPDF(email.id)}
                  disabled={exporting}
                  className="ml-4 inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                >
                  <ArrowDownTrayIcon className="h-4 w-4 mr-1" />
                  Export PDF
                </button>
              </div>
            </div>
          ))}

          {filteredAndSortedEmails().length === 0 && (
            <div className="p-4 text-center text-gray-500">
              No emails found matching your filters
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default HistoryViewer;
