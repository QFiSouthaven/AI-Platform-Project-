import React, { useState, useEffect, useCallback } from 'react';
import { getKafkaTopics, getTopicDetails, getConsumerGroups, getConsumerGroupDetails } from '../../services/integrationService';

const KafkaTopics = () => {
  const [topics, setTopics] = useState([]);
  const [consumerGroups, setConsumerGroups] = useState([]);
  const [selectedTopic, setSelectedTopic] = useState(null);
  const [selectedGroup, setSelectedGroup] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('topics');

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const [topicsData, groupsData] = await Promise.all([
        getKafkaTopics(),
        getConsumerGroups(),
      ]);
      setTopics(topicsData.data || []);
      setConsumerGroups(groupsData.data || []);
    } catch (error) {
      console.error('Failed to fetch Kafka data:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, [fetchData]);

  const handleTopicClick = async (topicName) => {
    try {
      const result = await getTopicDetails(topicName);
      setSelectedTopic(result.data);
    } catch (error) {
      console.error('Failed to fetch topic details:', error);
    }
  };

  const handleGroupClick = async (groupId) => {
    try {
      const result = await getConsumerGroupDetails(groupId);
      setSelectedGroup(result.data);
    } catch (error) {
      console.error('Failed to fetch group details:', error);
    }
  };

  const formatNumber = (num) => {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num?.toString() || '0';
  };

  const getHealthColor = (status) => {
    switch (status) {
      case 'healthy':
        return 'bg-green-100 text-green-800';
      case 'warning':
        return 'bg-yellow-100 text-yellow-800';
      case 'error':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Kafka Topics</h1>
          <p className="text-sm text-gray-500">Monitor Kafka topics and consumer groups</p>
        </div>
        <button
          onClick={fetchData}
          className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700"
        >
          Refresh
        </button>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg shadow-md p-6">
          <p className="text-sm font-medium text-gray-600">Total Topics</p>
          <p className="mt-1 text-3xl font-semibold text-gray-900">{topics.length}</p>
        </div>
        <div className="bg-white rounded-lg shadow-md p-6">
          <p className="text-sm font-medium text-gray-600">Total Partitions</p>
          <p className="mt-1 text-3xl font-semibold text-gray-900">
            {topics.reduce((sum, t) => sum + (t.partitions || 0), 0)}
          </p>
        </div>
        <div className="bg-white rounded-lg shadow-md p-6">
          <p className="text-sm font-medium text-gray-600">Consumer Groups</p>
          <p className="mt-1 text-3xl font-semibold text-gray-900">{consumerGroups.length}</p>
        </div>
        <div className="bg-white rounded-lg shadow-md p-6">
          <p className="text-sm font-medium text-gray-600">Total Messages</p>
          <p className="mt-1 text-3xl font-semibold text-gray-900">
            {formatNumber(topics.reduce((sum, t) => sum + (t.message_count || 0), 0))}
          </p>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('topics')}
            className={`py-4 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'topics'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Topics
          </button>
          <button
            onClick={() => setActiveTab('consumers')}
            className={`py-4 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'consumers'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Consumer Groups
          </button>
        </nav>
      </div>

      {/* Topics Tab */}
      {activeTab === 'topics' && (
        <div className="bg-white rounded-lg shadow-md overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Topic Name
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Partitions
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Replication
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Messages
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {loading ? (
                  <tr>
                    <td colSpan="6" className="px-6 py-4 text-center text-gray-500">
                      Loading topics...
                    </td>
                  </tr>
                ) : topics.length === 0 ? (
                  <tr>
                    <td colSpan="6" className="px-6 py-4 text-center text-gray-500">
                      No topics found
                    </td>
                  </tr>
                ) : (
                  topics.map((topic) => (
                    <tr key={topic.name} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="text-sm font-medium text-gray-900">{topic.name}</span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {topic.partitions}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {topic.replication_factor}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {formatNumber(topic.message_count)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${getHealthColor(topic.status)}`}>
                          {topic.status || 'unknown'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <button
                          onClick={() => handleTopicClick(topic.name)}
                          className="text-blue-600 hover:text-blue-900"
                        >
                          View Details
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Consumer Groups Tab */}
      {activeTab === 'consumers' && (
        <div className="bg-white rounded-lg shadow-md overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Group ID
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Members
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Topics
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Lag
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    State
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {loading ? (
                  <tr>
                    <td colSpan="6" className="px-6 py-4 text-center text-gray-500">
                      Loading consumer groups...
                    </td>
                  </tr>
                ) : consumerGroups.length === 0 ? (
                  <tr>
                    <td colSpan="6" className="px-6 py-4 text-center text-gray-500">
                      No consumer groups found
                    </td>
                  </tr>
                ) : (
                  consumerGroups.map((group) => (
                    <tr key={group.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="text-sm font-medium text-gray-900">{group.id}</span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {group.members}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {group.topics?.length || 0}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`text-sm ${group.lag > 1000 ? 'text-red-600 font-medium' : 'text-gray-500'}`}>
                          {formatNumber(group.lag)}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${
                          group.state === 'Stable' ? 'bg-green-100 text-green-800' :
                          group.state === 'Empty' ? 'bg-gray-100 text-gray-800' :
                          'bg-yellow-100 text-yellow-800'
                        }`}>
                          {group.state}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <button
                          onClick={() => handleGroupClick(group.id)}
                          className="text-blue-600 hover:text-blue-900"
                        >
                          View Details
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Topic Detail Modal */}
      {selectedTopic && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-center justify-center min-h-screen px-4">
            <div className="fixed inset-0 bg-gray-500 bg-opacity-75" onClick={() => setSelectedTopic(null)} />
            <div className="relative bg-white rounded-lg shadow-xl max-w-3xl w-full p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900">Topic: {selectedTopic.name}</h3>
                <button
                  onClick={() => setSelectedTopic(null)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              <div className="grid grid-cols-2 gap-4 mb-6">
                <div className="bg-gray-50 p-4 rounded-lg">
                  <p className="text-sm text-gray-500">Partitions</p>
                  <p className="text-lg font-semibold">{selectedTopic.partitions}</p>
                </div>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <p className="text-sm text-gray-500">Replication Factor</p>
                  <p className="text-lg font-semibold">{selectedTopic.replication_factor}</p>
                </div>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <p className="text-sm text-gray-500">Total Messages</p>
                  <p className="text-lg font-semibold">{formatNumber(selectedTopic.message_count)}</p>
                </div>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <p className="text-sm text-gray-500">Retention (ms)</p>
                  <p className="text-lg font-semibold">{selectedTopic.retention_ms || 'Default'}</p>
                </div>
              </div>

              {selectedTopic.partitions_info && (
                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-3">Partition Details</h4>
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Partition</th>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Leader</th>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Replicas</th>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">ISR</th>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Offset</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-200">
                        {selectedTopic.partitions_info.map((partition) => (
                          <tr key={partition.id}>
                            <td className="px-4 py-2 text-sm text-gray-900">{partition.id}</td>
                            <td className="px-4 py-2 text-sm text-gray-500">{partition.leader}</td>
                            <td className="px-4 py-2 text-sm text-gray-500">{partition.replicas?.join(', ')}</td>
                            <td className="px-4 py-2 text-sm text-gray-500">{partition.isr?.join(', ')}</td>
                            <td className="px-4 py-2 text-sm text-gray-500">{formatNumber(partition.offset)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              <div className="mt-6 flex justify-end">
                <button
                  onClick={() => setSelectedTopic(null)}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Consumer Group Detail Modal */}
      {selectedGroup && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-center justify-center min-h-screen px-4">
            <div className="fixed inset-0 bg-gray-500 bg-opacity-75" onClick={() => setSelectedGroup(null)} />
            <div className="relative bg-white rounded-lg shadow-xl max-w-3xl w-full p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900">Consumer Group: {selectedGroup.id}</h3>
                <button
                  onClick={() => setSelectedGroup(null)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              <div className="grid grid-cols-3 gap-4 mb-6">
                <div className="bg-gray-50 p-4 rounded-lg">
                  <p className="text-sm text-gray-500">State</p>
                  <p className="text-lg font-semibold">{selectedGroup.state}</p>
                </div>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <p className="text-sm text-gray-500">Members</p>
                  <p className="text-lg font-semibold">{selectedGroup.members}</p>
                </div>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <p className="text-sm text-gray-500">Total Lag</p>
                  <p className={`text-lg font-semibold ${selectedGroup.lag > 1000 ? 'text-red-600' : ''}`}>
                    {formatNumber(selectedGroup.lag)}
                  </p>
                </div>
              </div>

              {selectedGroup.members_info && (
                <div className="mb-6">
                  <h4 className="text-sm font-medium text-gray-700 mb-3">Members</h4>
                  <div className="space-y-2">
                    {selectedGroup.members_info.map((member, index) => (
                      <div key={index} className="bg-gray-50 p-3 rounded-lg">
                        <p className="text-sm font-medium text-gray-900">{member.client_id}</p>
                        <p className="text-xs text-gray-500">{member.host}</p>
                        <p className="text-xs text-gray-500">
                          Partitions: {member.partitions?.join(', ') || 'None'}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {selectedGroup.topic_lag && (
                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-3">Lag by Topic</h4>
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Topic</th>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Partition</th>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Current Offset</th>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Log End Offset</th>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Lag</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-200">
                        {selectedGroup.topic_lag.map((item, index) => (
                          <tr key={index}>
                            <td className="px-4 py-2 text-sm text-gray-900">{item.topic}</td>
                            <td className="px-4 py-2 text-sm text-gray-500">{item.partition}</td>
                            <td className="px-4 py-2 text-sm text-gray-500">{formatNumber(item.current_offset)}</td>
                            <td className="px-4 py-2 text-sm text-gray-500">{formatNumber(item.log_end_offset)}</td>
                            <td className={`px-4 py-2 text-sm ${item.lag > 100 ? 'text-red-600 font-medium' : 'text-gray-500'}`}>
                              {formatNumber(item.lag)}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              <div className="mt-6 flex justify-end">
                <button
                  onClick={() => setSelectedGroup(null)}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default KafkaTopics;
