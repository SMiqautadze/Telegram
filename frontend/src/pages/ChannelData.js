import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';
import LoadingSpinner from '../components/LoadingSpinner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const ChannelData = () => {
  const { channelId } = useParams();
  const { token } = useAuth();
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [exporting, setExporting] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');
  const [page, setPage] = useState(1);
  const [searchTerm, setSearchTerm] = useState('');
  const [filteredMessages, setFilteredMessages] = useState([]);
  const [stats, setStats] = useState({
    totalMessages: 0,
    messagesWithMedia: 0,
    uniqueSenders: 0
  });

  // Pagination
  const messagesPerPage = 20;
  const totalPages = Math.ceil(filteredMessages.length / messagesPerPage);
  const currentMessages = filteredMessages.slice(
    (page - 1) * messagesPerPage,
    page * messagesPerPage
  );

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const response = await axios.get(`${BACKEND_URL}/channel-data/${channelId}`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        
        setMessages(response.data.messages || []);
        setFilteredMessages(response.data.messages || []);
        
        // Calculate statistics
        const data = response.data.messages || [];
        const messagesWithMedia = data.filter(msg => msg.media_type).length;
        const senderIds = new Set(data.map(msg => msg.sender_id));
        
        setStats({
          totalMessages: data.length,
          messagesWithMedia,
          uniqueSenders: senderIds.size
        });
      } catch (err) {
        console.error('Error fetching channel data:', err);
        setError('Failed to load channel data');
      } finally {
        setLoading(false);
      }
    };

    if (token && channelId) {
      fetchData();
    }
  }, [token, channelId]);

  useEffect(() => {
    if (searchTerm.trim() === '') {
      setFilteredMessages(messages);
    } else {
      const filtered = messages.filter(msg => 
        (msg.message && msg.message.toLowerCase().includes(searchTerm.toLowerCase())) ||
        (msg.first_name && msg.first_name.toLowerCase().includes(searchTerm.toLowerCase())) ||
        (msg.last_name && msg.last_name.toLowerCase().includes(searchTerm.toLowerCase())) ||
        (msg.username && msg.username.toLowerCase().includes(searchTerm.toLowerCase()))
      );
      setFilteredMessages(filtered);
    }
    setPage(1); // Reset to first page when search changes
  }, [searchTerm, messages]);

  const exportData = async (format) => {
    setExporting(true);
    setError('');
    setSuccessMessage('');
    
    try {
      const response = await axios.get(`${BACKEND_URL}/export-data/${channelId}/${format}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setSuccessMessage(`Data exported successfully in ${format.toUpperCase()} format`);
    } catch (err) {
      console.error(`Error exporting data as ${format}:`, err);
      setError(`Failed to export data as ${format}`);
    } finally {
      setExporting(false);
    }
  };

  const formatDate = (dateStr) => {
    const date = new Date(dateStr);
    return date.toLocaleString();
  };

  if (loading) {
    return <LoadingSpinner />;
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Channel Data: {channelId}</h1>
        <Link to="/channel-manager" className="mt-2 md:mt-0 btn btn-secondary">
          Back to Channel Manager
        </Link>
      </div>
      
      {error && (
        <div className="mb-4 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}
      
      {successMessage && (
        <div className="mb-4 bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded">
          {successMessage}
        </div>
      )}
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="text-center">
            <div className="text-4xl font-bold text-blue-600">{stats.totalMessages}</div>
            <div className="text-gray-500 mt-2">Total Messages</div>
          </div>
        </div>
        
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="text-center">
            <div className="text-4xl font-bold text-green-600">{stats.messagesWithMedia}</div>
            <div className="text-gray-500 mt-2">Media Files</div>
          </div>
        </div>
        
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="text-center">
            <div className="text-4xl font-bold text-purple-600">{stats.uniqueSenders}</div>
            <div className="text-gray-500 mt-2">Unique Senders</div>
          </div>
        </div>
      </div>
      
      <div className="bg-white rounded-lg shadow-md p-6 mb-8">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-4">
          <h2 className="text-xl font-semibold">Actions</h2>
          
          <div className="flex flex-col md:flex-row space-y-2 md:space-y-0 md:space-x-4 mt-2 md:mt-0">
            <button
              onClick={() => exportData('csv')}
              disabled={exporting}
              className="btn btn-primary"
            >
              {exporting ? 'Exporting...' : 'Export as CSV'}
            </button>
            
            <button
              onClick={() => exportData('json')}
              disabled={exporting}
              className="btn btn-primary"
            >
              {exporting ? 'Exporting...' : 'Export as JSON'}
            </button>
          </div>
        </div>
      </div>
      
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-6">
          <h2 className="text-xl font-semibold">Messages</h2>
          
          <div className="mt-2 md:mt-0">
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search messages..."
              className="px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </div>
        
        {messages.length === 0 ? (
          <div className="text-center py-6">
            <p className="text-gray-500">No messages found for this channel.</p>
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Sender</th>
                    <th>Message</th>
                    <th>Media</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {currentMessages.map((message) => (
                    <tr key={message.id}>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {formatDate(message.date)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {message.first_name && message.last_name 
                          ? `${message.first_name} ${message.last_name}` 
                          : message.first_name || message.last_name || (message.username ? `@${message.username}` : `User ${message.sender_id}`)}
                      </td>
                      <td className="px-6 py-4">
                        <div className="max-w-xs md:max-w-md truncate">
                          {message.message || "(No text content)"}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {message.media_type ? (
                          <span className="pill pill-blue">
                            {message.media_type.replace('MessageMedia', '')}
                          </span>
                        ) : (
                          <span className="text-gray-400">None</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            
            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-between mt-6">
                <div>
                  <p className="text-sm text-gray-700">
                    Showing {(page - 1) * messagesPerPage + 1} to {Math.min(page * messagesPerPage, filteredMessages.length)} of {filteredMessages.length} messages
                  </p>
                </div>
                
                <div className="flex space-x-2">
                  <button
                    onClick={() => setPage(Math.max(1, page - 1))}
                    disabled={page === 1}
                    className="px-3 py-1 rounded border border-gray-300 text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
                  >
                    Previous
                  </button>
                  
                  <button
                    onClick={() => setPage(Math.min(totalPages, page + 1))}
                    disabled={page === totalPages}
                    className="px-3 py-1 rounded border border-gray-300 text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
                  >
                    Next
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default ChannelData;
