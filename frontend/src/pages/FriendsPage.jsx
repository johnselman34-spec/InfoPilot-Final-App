/**
 * Friends Page Component
 * Manage friends, friend requests, and connections
 */
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';
import { User, Users, Check, X, Trash2, Loader2 } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { Layout } from '../components/layout/Layout';
import { FuturisticFrame } from '../components/common/FuturisticFrame';
import { API } from '../utils/constants';

const FriendsPage = () => {
  const { user } = useAuth();
  const [friends, setFriends] = useState([]);
  const [requests, setRequests] = useState({ incoming: [], outgoing: [] });
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    fetchFriends();
    fetchRequests();
  }, []);

  const fetchFriends = async () => {
    try {
      const res = await axios.get(`${API}/friends`);
      setFriends(res.data.friends || []);
    } catch (error) {
      console.error("Failed to fetch friends");
    } finally {
      setLoading(false);
    }
  };

  const fetchRequests = async () => {
    try {
      const res = await axios.get(`${API}/friends/requests`);
      setRequests(res.data);
    } catch (error) {
      console.error("Failed to fetch requests");
    }
  };

  const handleAccept = async (requestId) => {
    try {
      await axios.post(`${API}/friends/accept/${requestId}`);
      toast.success("Friend request accepted!");
      fetchFriends();
      fetchRequests();
    } catch (error) {
      toast.error("Failed to accept request");
    }
  };

  const handleReject = async (requestId) => {
    try {
      await axios.post(`${API}/friends/reject/${requestId}`);
      toast.success("Friend request rejected");
      fetchRequests();
    } catch (error) {
      toast.error("Failed to reject request");
    }
  };

  const handleRemove = async (friendId) => {
    if (!window.confirm("Remove this friend?")) return;
    try {
      await axios.delete(`${API}/friends/${friendId}`);
      toast.success("Friend removed");
      fetchFriends();
    } catch (error) {
      toast.error("Failed to remove friend");
    }
  };

  return (
    <Layout>
      <div className="max-w-4xl mx-auto space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-pink-400 to-purple-400 font-mono tracking-wider">FRIENDS</h1>
          <span className="px-3 py-1 bg-purple-500/20 border border-purple-500/50 text-purple-300 font-mono rounded">{friends.length} Friends</span>
        </div>

        {/* Friend Requests */}
        {requests.incoming.length > 0 && (
          <FuturisticFrame title="FRIEND REQUESTS" color="pink" className="bg-slate-900/80 border border-pink-500/30 rounded-lg">
            <div className="space-y-3">
              {requests.incoming.map((req) => (
                <div key={req.id} className="flex items-center justify-between p-3 bg-purple-500/10 rounded-lg">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-gradient-to-br from-pink-500/20 to-purple-500/20 rounded-full flex items-center justify-center">
                      <User className="w-5 h-5 text-pink-400" />
                    </div>
                    <span className="text-purple-300 font-mono">{req.from_username}</span>
                  </div>
                  <div className="flex gap-2">
                    <button onClick={() => handleAccept(req.id)} className="px-3 py-1 bg-green-600 text-white font-mono text-sm rounded hover:bg-green-700">
                      <Check className="w-4 h-4" />
                    </button>
                    <button onClick={() => handleReject(req.id)} className="px-3 py-1 bg-red-600 text-white font-mono text-sm rounded hover:bg-red-700">
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </FuturisticFrame>
        )}

        {/* Friends List */}
        <FuturisticFrame title="YOUR FRIENDS" color="purple" className="bg-slate-900/80 border border-purple-500/30 rounded-lg">
          {loading ? (
            <div className="flex justify-center py-8"><Loader2 className="w-8 h-8 text-pink-400 animate-spin" /></div>
          ) : friends.length === 0 ? (
            <div className="text-center py-8">
              <Users className="w-16 h-16 text-purple-400/30 mx-auto mb-4" />
              <p className="text-purple-400/60 font-mono">No friends yet</p>
              <p className="text-purple-400/40 font-mono text-sm mt-2">The admin has been added as your first friend!</p>
            </div>
          ) : (
            <div className="grid gap-3">
              {friends.map((friend) => (
                <div key={friend.id} className="flex items-center justify-between p-4 bg-purple-500/10 rounded-lg hover:bg-purple-500/20 transition-colors">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 bg-gradient-to-br from-pink-500/20 to-purple-500/20 rounded-full flex items-center justify-center border border-purple-500/30">
                      {friend.profile_photo ? (
                        <img src={friend.profile_photo} alt={friend.username} className="w-12 h-12 rounded-full object-cover" />
                      ) : (
                        <User className="w-6 h-6 text-pink-400" />
                      )}
                    </div>
                    <div>
                      <p className="text-purple-300 font-mono font-bold">{friend.username}</p>
                      {friend.is_admin && <span className="text-xs text-pink-400 font-mono">ADMIN</span>}
                    </div>
                  </div>
                  <button onClick={() => handleRemove(friend.id)} className="p-2 text-red-400/60 hover:text-red-400 hover:bg-red-500/10 rounded">
                    <Trash2 className="w-5 h-5" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </FuturisticFrame>
      </div>
    </Layout>
  );
};

export default FriendsPage;
