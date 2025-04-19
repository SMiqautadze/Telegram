import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';
import LoadingSpinner from '../components/LoadingSpinner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const Dashboard = () => {
  const { currentUser, token } = useAuth();
  const [channels, setChannels] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [telegramSetupComplete, setTelegramSetupComplete] = useState(false);
  const [stats, setStats] = useState({
    totalChannels: 0,
    totalMessages: 0,
    totalMedia: 0
  });

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        // Check if Telegram credentials are set
        try {
          const telegramResponse = await axios.get(`${BACKEND_URL}/telegram-credentials`, {
            headers: { Authorization: `Bearer ${token}` }
          });
          setTelegramSetupComplete(true);
        } catch (error) {
          setTelegramSetupComplete(false);
        }
        
        // Get channels
        const channelsResponse = await axios.get(`${BACKEND_URL}/channels`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        
        setChannels(channelsResponse.data.channels || {});
        
        // Calculate stats
        let totalMessages = 0;
        let totalMedia = 0;
        
        const channelIds = Object.keys(channelsResponse.data.channels || {});
        
        for (const channelId of channelIds) {
          try {
            const dataResponse = await axios.get(`${BACKEND_URL}/channel-data/${channelId}`, {
              headers: { Authorization: `Bearer ${token}` }
            });
            
            const messages = dataResponse.data.messages || [];
            totalMessages += messages.length;
            
            // Count media files
            const mediaCount = messages.filter(msg => msg.media_type).length;
            totalMedia += mediaCount;
          } catch (error) {
            console.error(`Error fetching data for channel ${channelId}:`, error);
          }
        }
        
        setStats({
          totalChannels: channelIds.length,
          totalMessages,
          totalMedia
        });
        
      } catch (err) {
        console.error('Error fetching dashboard data:', err);
        setError('Failed to load dashboard data');
      } finally {
        setLoading(false);
      }
    };

    if (token) {
      fetchData();
    }
  }, [token]);

  if (loading) {
    return <LoadingSpinner />;
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <div className="mb-10">
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="mt-2 text-gray-600">
          Welcome back, {currentUser?.full_name || currentUser?.email}
        </p>
      </div>
      
      {error && (
        <div className="mb-6 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}
      
      {!telegramSetupComplete && (
        <div className="mb-8 bg-yellow-100 border border-yellow-400 text-yellow-800 px-4 py-3 rounded">
          <p className="font-medium">Telegram Setup Required</p>
          <p className="mt-1">You need to set up your Telegram API credentials to start scraping channels.</p>
          <Link to="/telegram-setup" className="mt-2 inline-block btn btn-primary">
            Set Up Telegram Credentials
          </Link>
        </div>
      )}
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
        <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg shadow-md p-6 text-white">
          <h3 className="text-lg font-semibold mb-2">Channels</h3>
          <p className="text-3xl font-bold">{stats.totalChannels}</p>
          <p className="mt-2 text-blue-100">Total channels being scraped</p>
        </div>
        
        <div className="bg-gradient-to-br from-green-500 to-green-600 rounded-lg shadow-md p-6 text-white">
          <h3 className="text-lg font-semibold mb-2">Messages</h3>
          <p className="text-3xl font-bold">{stats.totalMessages}</p>
          <p className="mt-2 text-green-100">Total messages scraped</p>
        </div>
        
        <div className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-lg shadow-md p-6 text-white">
          <h3 className="text-lg font-semibold mb-2">Media Files</h3>
          <p className="text-3xl font-bold">{stats.totalMedia}</p>
          <p className="mt-2 text-purple-100">Total media files downloaded</p>
        </div>
      </div>
      
      <div className="bg-white rounded-lg shadow-md p-6 mb-10">
        <h2 className="text-xl font-semibold mb-4">Your Channels</h2>
        
        {Object.keys(channels).length === 0 ? (
          <div className="text-center py-6">
            <p className="text-gray-500 mb-4">You haven't added any channels yet.</p>
            <Link to="/channel-manager" className="btn btn-primary">
              Add Channels
            </Link>
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
                      <Link 
                        to={`/channel-data/${channelId}`}
                        className="text-blue-600 hover:text-blue-900 mr-4"
                      >
                        View Data
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4">Quick Actions</h2>
          <div className="space-y-3">
            <Link to="/channel-manager" className="block w-full text-center btn btn-primary">
              Manage Channels
            </Link>
            <Link to="/telegram-setup" className="block w-full text-center btn btn-secondary">
              Telegram Setup
            </Link>
          </div>
        </div>
        
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4">Recent Activity</h2>
          <p className="text-gray-500 italic text-center py-10">
            Activity tracking coming soon...
          </p>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
