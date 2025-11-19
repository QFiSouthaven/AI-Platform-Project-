import React, { useState, useEffect, useRef } from 'react';
import { useParams } from 'react-router-dom';
import { useAuth } from '../../components/auth/AuthContext';
import authService from '../../services/authService';

const UserProfile = () => {
  const { id } = useParams();
  const { user: currentUser, updateUser } = useAuth();
  const fileInputRef = useRef(null);

  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('profile');

  // Profile Form State
  const [profileData, setProfileData] = useState({
    fullName: '',
    email: '',
    phone: '',
    company: '',
    bio: ''
  });
  const [profileErrors, setProfileErrors] = useState({});
  const [isSavingProfile, setIsSavingProfile] = useState(false);
  const [profileSuccess, setProfileSuccess] = useState('');

  // Password Form State
  const [passwordData, setPasswordData] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: ''
  });
  const [passwordErrors, setPasswordErrors] = useState({});
  const [isSavingPassword, setIsSavingPassword] = useState(false);
  const [passwordSuccess, setPasswordSuccess] = useState('');

  // API Keys State
  const [apiKeys, setApiKeys] = useState([]);
  const [newKeyName, setNewKeyName] = useState('');
  const [isCreatingKey, setIsCreatingKey] = useState(false);
  const [showNewKey, setShowNewKey] = useState(null);

  // Activity History
  const [activities, setActivities] = useState([]);

  useEffect(() => {
    fetchUserData();
  }, [id]);

  const fetchUserData = async () => {
    setIsLoading(true);
    try {
      const userId = id || currentUser?.id;
      const response = await authService.getCurrentUser();
      const userData = response.data || {
        id: userId,
        fullName: 'John Doe',
        email: 'john@example.com',
        phone: '+1 234 567 8900',
        company: 'AI Platform Inc.',
        bio: 'Full-stack developer passionate about AI',
        avatar: null,
        createdAt: '2024-01-15'
      };
      setUser(userData);
      setProfileData({
        fullName: userData.fullName || '',
        email: userData.email || '',
        phone: userData.phone || '',
        company: userData.company || '',
        bio: userData.bio || ''
      });

      // Mock API keys
      setApiKeys([
        { id: 1, name: 'Production API Key', key: 'sk-...a1b2', created: '2024-01-10', lastUsed: '2024-01-15' },
        { id: 2, name: 'Development Key', key: 'sk-...c3d4', created: '2024-01-12', lastUsed: '2024-01-14' }
      ]);

      // Mock activities
      setActivities([
        { id: 1, action: 'Logged in', timestamp: '2024-01-15 10:30:00', ip: '192.168.1.1' },
        { id: 2, action: 'Updated profile', timestamp: '2024-01-15 09:15:00', ip: '192.168.1.1' },
        { id: 3, action: 'Created API key', timestamp: '2024-01-12 14:00:00', ip: '192.168.1.1' },
        { id: 4, action: 'Changed password', timestamp: '2024-01-10 11:45:00', ip: '192.168.1.2' }
      ]);
    } catch (err) {
      console.error('Failed to fetch user data:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAvatarClick = () => {
    fileInputRef.current?.click();
  };

  const handleAvatarChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    // Validate file
    if (!file.type.startsWith('image/')) {
      alert('Please upload an image file');
      return;
    }
    if (file.size > 5 * 1024 * 1024) {
      alert('File size must be less than 5MB');
      return;
    }

    try {
      const formData = new FormData();
      formData.append('avatar', file);
      // await authService.updateAvatar(formData);

      // Preview
      const reader = new FileReader();
      reader.onload = (e) => {
        setUser(prev => ({ ...prev, avatar: e.target.result }));
      };
      reader.readAsDataURL(file);
    } catch (err) {
      alert('Failed to upload avatar');
    }
  };

  const handleProfileChange = (e) => {
    const { name, value } = e.target;
    setProfileData(prev => ({ ...prev, [name]: value }));
    if (profileErrors[name]) {
      setProfileErrors(prev => ({ ...prev, [name]: '' }));
    }
    setProfileSuccess('');
  };

  const handleProfileSubmit = async (e) => {
    e.preventDefault();

    const errors = {};
    if (!profileData.fullName.trim()) errors.fullName = 'Name is required';
    if (!profileData.email) errors.email = 'Email is required';
    if (profileData.email && !/\S+@\S+\.\S+/.test(profileData.email)) {
      errors.email = 'Invalid email format';
    }

    if (Object.keys(errors).length > 0) {
      setProfileErrors(errors);
      return;
    }

    setIsSavingProfile(true);
    try {
      await authService.updateProfile(profileData);
      setProfileSuccess('Profile updated successfully');
      if (updateUser) updateUser({ ...currentUser, ...profileData });
    } catch (err) {
      setProfileErrors({ submit: 'Failed to update profile' });
    } finally {
      setIsSavingProfile(false);
    }
  };

  const handlePasswordChange = (e) => {
    const { name, value } = e.target;
    setPasswordData(prev => ({ ...prev, [name]: value }));
    if (passwordErrors[name]) {
      setPasswordErrors(prev => ({ ...prev, [name]: '' }));
    }
    setPasswordSuccess('');
  };

  const handlePasswordSubmit = async (e) => {
    e.preventDefault();

    const errors = {};
    if (!passwordData.currentPassword) errors.currentPassword = 'Current password is required';
    if (!passwordData.newPassword) errors.newPassword = 'New password is required';
    if (passwordData.newPassword.length < 8) errors.newPassword = 'Password must be at least 8 characters';
    if (passwordData.newPassword !== passwordData.confirmPassword) {
      errors.confirmPassword = 'Passwords do not match';
    }

    if (Object.keys(errors).length > 0) {
      setPasswordErrors(errors);
      return;
    }

    setIsSavingPassword(true);
    try {
      await authService.changePassword(passwordData.currentPassword, passwordData.newPassword);
      setPasswordSuccess('Password changed successfully');
      setPasswordData({ currentPassword: '', newPassword: '', confirmPassword: '' });
    } catch (err) {
      setPasswordErrors({ submit: err.response?.data?.message || 'Failed to change password' });
    } finally {
      setIsSavingPassword(false);
    }
  };

  const handleCreateApiKey = async () => {
    if (!newKeyName.trim()) return;

    setIsCreatingKey(true);
    try {
      // const response = await authService.createApiKey(newKeyName);
      const newKey = {
        id: Date.now(),
        name: newKeyName,
        key: `sk-${Math.random().toString(36).substring(2, 34)}`,
        created: new Date().toISOString().split('T')[0],
        lastUsed: 'Never'
      };
      setApiKeys(prev => [...prev, { ...newKey, key: `sk-...${newKey.key.slice(-4)}` }]);
      setShowNewKey(newKey.key);
      setNewKeyName('');
    } catch (err) {
      alert('Failed to create API key');
    } finally {
      setIsCreatingKey(false);
    }
  };

  const handleDeleteApiKey = async (keyId) => {
    if (!window.confirm('Are you sure you want to delete this API key?')) return;

    try {
      // await authService.deleteApiKey(keyId);
      setApiKeys(prev => prev.filter(key => key.id !== keyId));
    } catch (err) {
      alert('Failed to delete API key');
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-purple-500"></div>
      </div>
    );
  }

  return (
    <div className="p-6 bg-gray-50 dark:bg-gray-900 min-h-screen">
      <div className="max-w-4xl mx-auto">
        {/* Profile Header */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 mb-6">
          <div className="flex items-center">
            <div className="relative">
              <div
                onClick={handleAvatarClick}
                className="w-24 h-24 rounded-full bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center cursor-pointer hover:opacity-80 transition overflow-hidden"
              >
                {user?.avatar ? (
                  <img src={user.avatar} alt="Avatar" className="w-full h-full object-cover" />
                ) : (
                  <span className="text-4xl text-purple-600 dark:text-purple-400 font-bold">
                    {user?.fullName?.charAt(0).toUpperCase() || 'U'}
                  </span>
                )}
              </div>
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                onChange={handleAvatarChange}
                className="hidden"
              />
              <button
                onClick={handleAvatarClick}
                className="absolute bottom-0 right-0 p-1 bg-purple-600 rounded-full text-white hover:bg-purple-700 transition"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
              </button>
            </div>
            <div className="ml-6">
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white">{user?.fullName}</h1>
              <p className="text-gray-500 dark:text-gray-400">{user?.email}</p>
              <p className="text-sm text-gray-400 dark:text-gray-500 mt-1">
                Member since {new Date(user?.createdAt).toLocaleDateString()}
              </p>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
          <div className="border-b border-gray-200 dark:border-gray-700">
            <nav className="flex -mb-px">
              {[
                { id: 'profile', label: 'Profile' },
                { id: 'password', label: 'Password' },
                { id: 'api-keys', label: 'API Keys' },
                { id: 'activity', label: 'Activity' }
              ].map(tab => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`px-6 py-4 text-sm font-medium border-b-2 transition ${
                    activeTab === tab.id
                      ? 'border-purple-600 text-purple-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </nav>
          </div>

          <div className="p-6">
            {/* Profile Tab */}
            {activeTab === 'profile' && (
              <form onSubmit={handleProfileSubmit} className="space-y-6">
                {profileSuccess && (
                  <div className="p-3 bg-green-100 text-green-700 rounded-lg">{profileSuccess}</div>
                )}
                {profileErrors.submit && (
                  <div className="p-3 bg-red-100 text-red-700 rounded-lg">{profileErrors.submit}</div>
                )}

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Full Name
                    </label>
                    <input
                      type="text"
                      name="fullName"
                      value={profileData.fullName}
                      onChange={handleProfileChange}
                      className={`w-full px-4 py-2 border ${
                        profileErrors.fullName ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'
                      } rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500`}
                    />
                    {profileErrors.fullName && (
                      <p className="mt-1 text-sm text-red-500">{profileErrors.fullName}</p>
                    )}
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Email
                    </label>
                    <input
                      type="email"
                      name="email"
                      value={profileData.email}
                      onChange={handleProfileChange}
                      className={`w-full px-4 py-2 border ${
                        profileErrors.email ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'
                      } rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500`}
                    />
                    {profileErrors.email && (
                      <p className="mt-1 text-sm text-red-500">{profileErrors.email}</p>
                    )}
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Phone
                    </label>
                    <input
                      type="tel"
                      name="phone"
                      value={profileData.phone}
                      onChange={handleProfileChange}
                      className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Company
                    </label>
                    <input
                      type="text"
                      name="company"
                      value={profileData.company}
                      onChange={handleProfileChange}
                      className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Bio
                  </label>
                  <textarea
                    name="bio"
                    value={profileData.bio}
                    onChange={handleProfileChange}
                    rows={4}
                    className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500"
                  />
                </div>

                <div className="flex justify-end">
                  <button
                    type="submit"
                    disabled={isSavingProfile}
                    className="px-6 py-2 bg-purple-600 text-white font-medium rounded-lg hover:bg-purple-700 transition disabled:opacity-50"
                  >
                    {isSavingProfile ? 'Saving...' : 'Save Changes'}
                  </button>
                </div>
              </form>
            )}

            {/* Password Tab */}
            {activeTab === 'password' && (
              <form onSubmit={handlePasswordSubmit} className="space-y-6 max-w-md">
                {passwordSuccess && (
                  <div className="p-3 bg-green-100 text-green-700 rounded-lg">{passwordSuccess}</div>
                )}
                {passwordErrors.submit && (
                  <div className="p-3 bg-red-100 text-red-700 rounded-lg">{passwordErrors.submit}</div>
                )}

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Current Password
                  </label>
                  <input
                    type="password"
                    name="currentPassword"
                    value={passwordData.currentPassword}
                    onChange={handlePasswordChange}
                    className={`w-full px-4 py-2 border ${
                      passwordErrors.currentPassword ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'
                    } rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500`}
                  />
                  {passwordErrors.currentPassword && (
                    <p className="mt-1 text-sm text-red-500">{passwordErrors.currentPassword}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    New Password
                  </label>
                  <input
                    type="password"
                    name="newPassword"
                    value={passwordData.newPassword}
                    onChange={handlePasswordChange}
                    className={`w-full px-4 py-2 border ${
                      passwordErrors.newPassword ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'
                    } rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500`}
                  />
                  {passwordErrors.newPassword && (
                    <p className="mt-1 text-sm text-red-500">{passwordErrors.newPassword}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Confirm New Password
                  </label>
                  <input
                    type="password"
                    name="confirmPassword"
                    value={passwordData.confirmPassword}
                    onChange={handlePasswordChange}
                    className={`w-full px-4 py-2 border ${
                      passwordErrors.confirmPassword ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'
                    } rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500`}
                  />
                  {passwordErrors.confirmPassword && (
                    <p className="mt-1 text-sm text-red-500">{passwordErrors.confirmPassword}</p>
                  )}
                </div>

                <div className="flex justify-end">
                  <button
                    type="submit"
                    disabled={isSavingPassword}
                    className="px-6 py-2 bg-purple-600 text-white font-medium rounded-lg hover:bg-purple-700 transition disabled:opacity-50"
                  >
                    {isSavingPassword ? 'Updating...' : 'Update Password'}
                  </button>
                </div>
              </form>
            )}

            {/* API Keys Tab */}
            {activeTab === 'api-keys' && (
              <div className="space-y-6">
                {/* New Key Modal */}
                {showNewKey && (
                  <div className="p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
                    <p className="text-sm font-medium text-green-800 dark:text-green-200 mb-2">
                      Your new API key has been created. Copy it now - you won't be able to see it again!
                    </p>
                    <div className="flex items-center gap-2">
                      <code className="flex-1 p-2 bg-white dark:bg-gray-800 rounded text-sm font-mono">
                        {showNewKey}
                      </code>
                      <button
                        onClick={() => {
                          navigator.clipboard.writeText(showNewKey);
                          alert('Copied to clipboard!');
                        }}
                        className="px-3 py-2 bg-green-600 text-white rounded hover:bg-green-700 transition"
                      >
                        Copy
                      </button>
                      <button
                        onClick={() => setShowNewKey(null)}
                        className="px-3 py-2 bg-gray-200 dark:bg-gray-700 rounded hover:bg-gray-300 dark:hover:bg-gray-600 transition"
                      >
                        Done
                      </button>
                    </div>
                  </div>
                )}

                {/* Create New Key */}
                <div className="flex gap-2">
                  <input
                    type="text"
                    placeholder="API Key Name"
                    value={newKeyName}
                    onChange={(e) => setNewKeyName(e.target.value)}
                    className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500"
                  />
                  <button
                    onClick={handleCreateApiKey}
                    disabled={isCreatingKey || !newKeyName.trim()}
                    className="px-4 py-2 bg-purple-600 text-white font-medium rounded-lg hover:bg-purple-700 transition disabled:opacity-50"
                  >
                    {isCreatingKey ? 'Creating...' : 'Create Key'}
                  </button>
                </div>

                {/* Keys List */}
                <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
                  <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                    <thead className="bg-gray-50 dark:bg-gray-900">
                      <tr>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Key</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Created</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Last Used</th>
                        <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                      {apiKeys.map(key => (
                        <tr key={key.id}>
                          <td className="px-4 py-3 text-sm text-gray-900 dark:text-white">{key.name}</td>
                          <td className="px-4 py-3 text-sm font-mono text-gray-500 dark:text-gray-400">{key.key}</td>
                          <td className="px-4 py-3 text-sm text-gray-500 dark:text-gray-400">{key.created}</td>
                          <td className="px-4 py-3 text-sm text-gray-500 dark:text-gray-400">{key.lastUsed}</td>
                          <td className="px-4 py-3 text-right">
                            <button
                              onClick={() => handleDeleteApiKey(key.id)}
                              className="text-red-600 hover:text-red-800 dark:hover:text-red-400"
                            >
                              Delete
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Activity Tab */}
            {activeTab === 'activity' && (
              <div className="space-y-4">
                {activities.map(activity => (
                  <div
                    key={activity.id}
                    className="flex items-center justify-between p-4 border border-gray-200 dark:border-gray-700 rounded-lg"
                  >
                    <div>
                      <p className="text-sm font-medium text-gray-900 dark:text-white">{activity.action}</p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">IP: {activity.ip}</p>
                    </div>
                    <span className="text-sm text-gray-500 dark:text-gray-400">
                      {new Date(activity.timestamp).toLocaleString()}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default UserProfile;
