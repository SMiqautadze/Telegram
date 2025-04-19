import { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';
import LoadingSpinner from '../components/LoadingSpinner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const ChannelManager = () => {
  const { token } = useAuth();
  const [channels, setChannels] = useState({});
  const [availableChannels, setAvailableChannels] = useState([]);
  const [newChannelId, setNewChannelId] = useState('');
  const [loading, setLoading] = useState(true);
  const [fetching, setFetching] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [scrapeMedia, setScrapeMedia] = useState(true);
  const [isContinuousScraping, setIsContinuousScraping] = useState(false);
  const [scrapingChannel, setScrapingChannel] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        // Get channels
        const channelsResponse = await axios.get(`${BACKEND_URL}/channels`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        setChannels(channelsResponse.data.channels || {});
        
        // Get scrape settings
        const settingsResponse = await axios.get(`${BACKEND_URL}/scrape-settings`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        setScrapeMedia(settingsResponse.data.scrape_media);
      } catch (err) {
        console.error('Error fetching channel data:', err);
        setError('Failed to load channel data');
      } finally {
        setLoading(false);
      }
    };

    if (token) {
      fetchData();
    }
  }, [token]);

  const fetchAvailableChannels = async () => {
    setFetching(true);
    setError('');
    
    try {
      const response = await axios.get(`${BACKEND_URL}/channels-list`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setAvailableChannels(response.data.channels || []);
    } catch (err) {
      console.error('Error fetching available channels:', err);
      setError('Failed to fetch available channels. Make sure your Telegram credentials are set correctly.');
    } finally {
      setFetching(false);
    }
  };

  const addChannel = async () => {
    if (!newChannelId) {
      return setError('Please enter a channel ID');
    }
    
    setError('');
    setSuccess('');
    
    try {
      await axios.post(
        `${BACKEND_URL}/channels`,
        { channel_id: newChannelId, last_message_id: 0 },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      // Refresh channels
      const response = await axios.get(`${BACKEND_URL}/channels`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setChannels(response.data.channels || {});
      setNewChannelId('');
      setSuccess(`Channel ${newChannelId} added successfully`);
    } catch (err) {
      console.error('Error adding channel:', err);
      setError('Failed to add channel');
    }
  };

  const removeChannel = async (channelId) => {
    if (!window.confirm(`Are you sure you want to remove channel ${channelId}?`)) {
      return;
    }
    
    setError('');
    setSuccess('');
    
    try {
      await axios.delete(`${BACKEND_URL}/channels/${channelId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      // Refresh channels
      const response = await axios.get(`${BACKEND_URL}/channels`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setChannels(response.data.channels || {});
      setSuccess(`Channel ${channelId} removed successfully`);
    } catch (err) {
      console.error('Error removing channel:', err);
      setError('Failed to remove channel');
    }
  };

  const updateScrapeSettings = async () => {
    setError('');
    setSuccess('');
    
    try {
      await axios.post(
        `${BACKEND_URL}/scrape-settings`,
        { scrape_media: scrapeMedia },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      setSuccess('Scrape settings updated successfully');
    } catch (err) {
      console.error('Error updating scrape settings:', err);
      setError('Failed to update scrape settings');
    }
  };

  const startScraping = async (channelId) => {
    setError('');
    setSuccess('');
    setScrapingChannel(channelId);
    
    try {
      await axios.post(
        `${BACKEND_URL}/scrape/${channelId}`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      setSuccess(`Scraping started for channel ${channelId}`);
    } catch (err) {
      console.error('Error starting scraping:', err);
      setError('Failed to start scraping');
    } finally {
      setScrapingChannel(null);
    }
  };

  const toggleContinuousScraping = async () => {
    setError('');
    setSuccess('');
    
    try {
      if (isContinuousScraping) {
        await axios.post(
          `${BACKEND_URL}/continuous-scrape/stop`,
          {},
          { headers: { Authorization: `Bearer ${token}` } }
        );
        setSuccess('Continuous scraping stopped');
      } else {
        await axios.post(
          `${BACKEND_URL}/continuous-scrape/start`,
          {},
          { headers: { Authorization: `Bearer ${token}` } }
        );
        setSuccess('Continuous scraping started');
      }
      
      setIsContinuousScraping(!isContinuousScraping);
    } catch (err) {
      console.error('Error toggling continuous scraping:', err);
      setError('Failed to toggle continuous scraping');
    }
  };

  if (loading) {
    return <LoadingSpinner />;
  }

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <h1 className="text-3xl font-bold text-gray-900 mb-6">Channel Manager</h1>
      
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
      
      <div className="bg-white rounded-lg shadow-md p-6 mb-8">
        <h2 className="text-xl font-semibold mb-4">Add Channel</h2>
        
        <div className="space-y-4">
          <div>
            <label htmlFor="channelId" className="block text-sm font-medium text-gray-700">
              Channel ID or Username
            </label>
            <div className="mt-1">
              <input
                id="channelId"
                type="text"
                value={newChannelId}
                onChange={(e) => setNewChannelId(e.target.value)}
                className="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                placeholder="e.g., -100123456789 or channelname"
              />
            </div>
            <p className="mt-1 text-sm text-gray-500">
              Enter either the channel ID (e.g., -100123456789) or username (without @)
            </p>
          </div>
          
          <div className="flex space-x-4">
            <button
              onClick={addChannel}
              className="btn btn-primary"
            >
              Add Channel
            </button>
            
            <button
              onClick={fetchAvailableChannels}
              disabled={fetching}
              className="btn btn-secondary"
            >
              {fetching ? 'Fetching...' : 'Fetch Available Channels'}
            </button>
          </div>
        </div>
        
        {availableChannels.length > 0 && (
          <div className="mt-6">
            <h3 className="text-lg font-medium mb-2">Available Channels:</h3>
            <div className="bg-gray-50 p-4 rounded-md max-h-60 overflow-y-auto">
              <ul className="divide-y divide-gray-200">
                {availableChannels.map((channel) => (
                  <li key={channel.id} className="py-2">
                    <div className="flex justify-between items-center">
                      <div>
                        <p className="font-medium">{channel.title}</p>
                        <p className="text-sm text-gray-500">ID: {channel.id}</p>
                      </div>
                      <button
                        onClick={() => {
                          setNewChannelId(channel.id);
                        }}
                        className="text-sm text-blue-600 hover:text-blue-800"
                      >
                        Select
                      </button>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}
      </div>
      
      <div className="bg-white rounded-lg shadow-md p-6 mb-8">
        <h2 className="text-xl font-semibold mb-4">Scrape Settings</h2>
        
        <div className="mb-4">
          <div className="flex items-center">
            <input
              id="scrapeMedia"
              type="checkbox"
              checked={scrapeMedia}
              onChange={() => setScrapeMedia(!scrapeMedia)}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <label htmlFor="scrapeMedia" className="ml-2 block text-sm text-gray-900">
              Download media files (photos, documents)
            </label>
          </div>
          <p className="mt-1 text-sm text-gray-500 ml-6">
            Enabling this will download all media files from messages. Disabling will only store message text.
          </p>
        </div>
        
        <div className="flex space-x-4">
          <button
            onClick={updateScrapeSettings}
            className="btn btn-primary"
          >
            Save Settings
          </button>
          
          <button
            onClick={toggleContinuousScraping}
            className={`btn ${isContinuousScraping ? 'btn-danger' : 'btn-success'}`}
          >
            {isContinuousScraping ? 'Stop Continuous Scraping' : 'Start Continuous Scraping'}
          </button>
        </div>
      </div>
      
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold mb-4">Manage Channels</h2>
        
        {Object.keys(channels).length === 0 ? (
          <div className="text-center py-6">
            <p className="text-gray-500">You haven't added any channels yet.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead>
                <tr>
                  <th>Channel ID</th>
                  <th>Last Message ID</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {Object.entries(channels).map(([channelId, lastMessageId]) => (
                  <tr key={channelId}>
                    <td className="px-6 py-4 whitespace-nowrap">{channelId}</td>
                    <td className="px-6 py-4 whitespace-nowrap">{lastMessageId}</td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <button
                        onClick={() => startScraping(channelId)}
                        disabled={scrapingChannel === channelId}
                        className="text-blue-600 hover:text-blue-900 mr-4"
                      >
                        {scrapingChannel === channelId ? 'Scraping...' : 'Scrape Now'}
                      </button>
                      
                      <button
                        onClick={() => removeChannel(channelId)}
                        className="text-red-600 hover:text-red-900"
                      >
                        Remove
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default ChannelManager;
