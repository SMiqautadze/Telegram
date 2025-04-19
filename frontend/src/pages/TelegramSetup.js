import { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';
import LoadingSpinner from '../components/LoadingSpinner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const TelegramSetup = () => {
  const { token } = useAuth();
  const [apiId, setApiId] = useState('');
  const [apiHash, setApiHash] = useState('');
  const [phone, setPhone] = useState('');
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [hasCredentials, setHasCredentials] = useState(false);

  useEffect(() => {
    const fetchCredentials = async () => {
      setLoading(true);
      try {
        const response = await axios.get(`${BACKEND_URL}/telegram-credentials`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        
        if (response.data) {
          setApiId(response.data.api_id || '');
          setApiHash(response.data.api_hash || '');
          setPhone(response.data.phone || '');
          setHasCredentials(true);
        }
      } catch (err) {
        if (err.response && err.response.status !== 404) {
          setError('Failed to fetch Telegram credentials');
          console.error(err);
        }
      } finally {
        setLoading(false);
      }
    };

    if (token) {
      fetchCredentials();
    }
  }, [token]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Validate form
    if (!apiId || !apiHash || !phone) {
      return setError('All fields are required');
    }
    
    // Validate API ID is numeric
    if (!/^\d+$/.test(apiId)) {
      return setError('API ID must be a number');
    }
    
    // Validate phone format
    if (!/^\+?[0-9]{7,15}$/.test(phone)) {
      return setError('Phone number is invalid. Please include country code (e.g., +1234567890)');
    }
    
    setError('');
    setSuccess('');
    setSubmitting(true);
    
    try {
      await axios.post(
        `${BACKEND_URL}/telegram-credentials`,
        {
          api_id: parseInt(apiId),
          api_hash: apiHash,
          phone: phone
        },
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      
      setSuccess('Telegram credentials saved successfully');
      setHasCredentials(true);
    } catch (err) {
      console.error('Error saving Telegram credentials:', err);
      setError('Failed to save Telegram credentials');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return <LoadingSpinner />;
  }

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <h1 className="text-3xl font-bold text-gray-900 mb-6">Telegram Credentials Setup</h1>
      
      <div className="bg-white rounded-lg shadow-md p-6">
        {error && (
          <div className="mb-4 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
            {error}
          </div>
        )}
        
        {success && (
          <div className="mb-4 bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded">
            {success}
          </div>
        )}
        
        <div className="mb-6">
          <h2 className="text-xl font-semibold mb-2">How to get Telegram API credentials:</h2>
          <ol className="list-decimal pl-5 space-y-2">
            <li>Visit <a href="https://my.telegram.org/auth" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">https://my.telegram.org/auth</a></li>
            <li>Log in with your phone number</li>
            <li>Click on "API development tools"</li>
            <li>
              Fill in the form:
              <ul className="list-disc pl-5 mt-1">
                <li>App title: Your app name</li>
                <li>Short name: Your app short name</li>
                <li>Platform: Desktop</li>
                <li>Description: Brief description of your app</li>
              </ul>
            </li>
            <li>Click "Create application"</li>
            <li>You'll receive <code className="bg-gray-100 px-1">api_id</code> and <code className="bg-gray-100 px-1">api_hash</code> values</li>
          </ol>
        </div>
        
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label htmlFor="apiId" className="block text-sm font-medium text-gray-700">
              API ID
            </label>
            <div className="mt-1">
              <input
                id="apiId"
                name="apiId"
                type="text"
                required
                value={apiId}
                onChange={(e) => setApiId(e.target.value)}
                className="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                placeholder="Enter your API ID"
              />
            </div>
          </div>
          
          <div>
            <label htmlFor="apiHash" className="block text-sm font-medium text-gray-700">
              API Hash
            </label>
            <div className="mt-1">
              <input
                id="apiHash"
                name="apiHash"
                type="text"
                required
                value={apiHash}
                onChange={(e) => setApiHash(e.target.value)}
                className="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                placeholder="Enter your API Hash"
              />
            </div>
          </div>
          
          <div>
            <label htmlFor="phone" className="block text-sm font-medium text-gray-700">
              Phone Number (with country code)
            </label>
            <div className="mt-1">
              <input
                id="phone"
                name="phone"
                type="text"
                required
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                className="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                placeholder="e.g., +1234567890"
              />
            </div>
            <p className="mt-1 text-sm text-gray-500">
              Include country code (e.g., +1 for US, +44 for UK)
            </p>
          </div>
          
          <div>
            <button
              type="submit"
              disabled={submitting}
              className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
            >
              {submitting ? 'Saving...' : hasCredentials ? 'Update Credentials' : 'Save Credentials'}
            </button>
          </div>
        </form>
        
        {hasCredentials && (
          <div className="mt-6 bg-blue-50 border border-blue-200 rounded-md p-4">
            <h3 className="text-sm font-medium text-blue-800">Telegram Credentials Set</h3>
            <p className="mt-1 text-sm text-blue-700">
              Your Telegram API credentials are configured. You can now add and scrape channels.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default TelegramSetup;
