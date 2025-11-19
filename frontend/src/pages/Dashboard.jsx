import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import {
  ShieldCheckIcon,
  CubeTransparentIcon,
  CpuChipIcon,
  CircleStackIcon,
  CubeIcon,
  ServerStackIcon,
  PlayIcon,
  CloudArrowUpIcon,
  PlusIcon,
  ChartBarIcon,
  ClockIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  XCircleIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
} from '@heroicons/react/24/outline'
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts'
import { CHART_COLORS } from '../utils/constants'

// Mock data for demonstration
const moduleStatuses = [
  {
    id: 'gateway',
    name: 'User Gateway',
    description: 'Authentication & API',
    icon: ShieldCheckIcon,
    status: 'online',
    metrics: { requests: '12.5k', latency: '45ms' },
    color: 'blue',
    gradient: 'from-blue-500 to-blue-600',
    path: '/gateway',
  },
  {
    id: 'workflow',
    name: 'Workflow Orchestration',
    description: 'Task Scheduling',
    icon: CubeTransparentIcon,
    status: 'online',
    metrics: { active: 8, completed: 156 },
    color: 'purple',
    gradient: 'from-purple-500 to-purple-600',
    path: '/workflows',
  },
  {
    id: 'processing',
    name: 'Core Processing',
    description: 'AI Generation',
    icon: CpuChipIcon,
    status: 'online',
    metrics: { jobs: 23, gpu: '78%' },
    color: 'green',
    gradient: 'from-green-500 to-green-600',
    path: '/processing',
  },
  {
    id: 'data',
    name: 'Data Integration',
    description: 'Event Streaming',
    icon: CircleStackIcon,
    status: 'warning',
    metrics: { events: '45k/min', cache: '92%' },
    color: 'orange',
    gradient: 'from-orange-500 to-orange-600',
    path: '/data',
  },
  {
    id: 'models',
    name: 'Model Management',
    description: 'Storage & Versioning',
    icon: CubeIcon,
    status: 'online',
    metrics: { models: 34, deployed: 12 },
    color: 'pink',
    gradient: 'from-pink-500 to-pink-600',
    path: '/models',
  },
  {
    id: 'infra',
    name: 'Infrastructure',
    description: 'Scaling & Resources',
    icon: ServerStackIcon,
    status: 'online',
    metrics: { nodes: 6, cpu: '65%' },
    color: 'cyan',
    gradient: 'from-cyan-500 to-cyan-600',
    path: '/infrastructure',
  },
]

const recentActivity = [
  {
    id: 1,
    type: 'workflow_completed',
    message: 'Workflow "Data Pipeline v2" completed successfully',
    time: '2 minutes ago',
    icon: CheckCircleIcon,
    iconColor: 'text-green-500',
  },
  {
    id: 2,
    type: 'model_deployed',
    message: 'Model "GPT-CodeGen-v3" deployed to production',
    time: '15 minutes ago',
    icon: CloudArrowUpIcon,
    iconColor: 'text-blue-500',
  },
  {
    id: 3,
    type: 'warning',
    message: 'High memory usage detected in Data Integration module',
    time: '32 minutes ago',
    icon: ExclamationTriangleIcon,
    iconColor: 'text-yellow-500',
  },
  {
    id: 4,
    type: 'workflow_started',
    message: 'Workflow "ML Training Pipeline" started',
    time: '1 hour ago',
    icon: PlayIcon,
    iconColor: 'text-purple-500',
  },
  {
    id: 5,
    type: 'user_login',
    message: 'New API key generated for service account',
    time: '2 hours ago',
    icon: ShieldCheckIcon,
    iconColor: 'text-indigo-500',
  },
]

// Chart data
const requestsData = [
  { time: '00:00', requests: 4000, errors: 50 },
  { time: '04:00', requests: 3000, errors: 30 },
  { time: '08:00', requests: 8000, errors: 80 },
  { time: '12:00', requests: 12000, errors: 120 },
  { time: '16:00', requests: 11000, errors: 90 },
  { time: '20:00', requests: 9000, errors: 70 },
  { time: 'Now', requests: 10500, errors: 85 },
]

const resourceUsageData = [
  { name: 'CPU', value: 65, color: CHART_COLORS.primary },
  { name: 'Memory', value: 78, color: CHART_COLORS.success },
  { name: 'Storage', value: 42, color: CHART_COLORS.warning },
  { name: 'Network', value: 88, color: CHART_COLORS.info },
]

const workflowStats = [
  { name: 'Mon', completed: 24, failed: 2 },
  { name: 'Tue', completed: 32, failed: 1 },
  { name: 'Wed', completed: 28, failed: 3 },
  { name: 'Thu', completed: 36, failed: 2 },
  { name: 'Fri', completed: 30, failed: 1 },
  { name: 'Sat', completed: 18, failed: 0 },
  { name: 'Sun', completed: 12, failed: 1 },
]

function StatusBadge({ status }) {
  const statusConfig = {
    online: {
      bg: 'bg-green-100',
      text: 'text-green-800',
      dot: 'bg-green-500',
      label: 'Online',
    },
    offline: {
      bg: 'bg-red-100',
      text: 'text-red-800',
      dot: 'bg-red-500',
      label: 'Offline',
    },
    warning: {
      bg: 'bg-yellow-100',
      text: 'text-yellow-800',
      dot: 'bg-yellow-500',
      label: 'Warning',
    },
  }

  const config = statusConfig[status] || statusConfig.offline

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2 py-1 text-xs font-medium ${config.bg} ${config.text}`}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${config.dot} animate-pulse`} />
      {config.label}
    </span>
  )
}

function ModuleCard({ module }) {
  return (
    <Link
      to={module.path}
      className="card group relative overflow-hidden p-6 transition-all duration-300 hover:-translate-y-1"
    >
      {/* Gradient accent */}
      <div
        className={`absolute inset-x-0 top-0 h-1 bg-gradient-to-r ${module.gradient}`}
      />

      <div className="flex items-start justify-between">
        <div className="flex items-center gap-4">
          <div
            className={`flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br ${module.gradient} shadow-lg`}
          >
            <module.icon className="h-6 w-6 text-white" />
          </div>
          <div>
            <h3 className="font-semibold text-gray-900">{module.name}</h3>
            <p className="text-sm text-gray-500">{module.description}</p>
          </div>
        </div>
        <StatusBadge status={module.status} />
      </div>

      {/* Metrics */}
      <div className="mt-4 grid grid-cols-2 gap-4">
        {Object.entries(module.metrics).map(([key, value]) => (
          <div key={key} className="text-center">
            <p className="text-lg font-bold text-gray-900">{value}</p>
            <p className="text-xs capitalize text-gray-500">{key}</p>
          </div>
        ))}
      </div>
    </Link>
  )
}

function QuickAction({ icon: Icon, label, onClick, gradient }) {
  return (
    <button
      onClick={onClick}
      className={`flex flex-col items-center gap-2 rounded-xl bg-gradient-to-br ${gradient} p-4 text-white shadow-lg transition-all duration-200 hover:scale-105 hover:shadow-xl`}
    >
      <Icon className="h-6 w-6" />
      <span className="text-sm font-medium">{label}</span>
    </button>
  )
}

function StatCard({ title, value, change, changeType, icon: Icon }) {
  return (
    <div className="card p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-500">{title}</p>
          <p className="mt-1 text-3xl font-bold text-gray-900">{value}</p>
        </div>
        <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary-100">
          <Icon className="h-6 w-6 text-primary-600" />
        </div>
      </div>
      {change && (
        <div className="mt-4 flex items-center gap-1">
          {changeType === 'increase' ? (
            <ArrowTrendingUpIcon className="h-4 w-4 text-green-500" />
          ) : (
            <ArrowTrendingDownIcon className="h-4 w-4 text-red-500" />
          )}
          <span
            className={`text-sm font-medium ${
              changeType === 'increase' ? 'text-green-600' : 'text-red-600'
            }`}
          >
            {change}
          </span>
          <span className="text-sm text-gray-500">vs last week</span>
        </div>
      )}
    </div>
  )
}

function Dashboard() {
  const [currentTime, setCurrentTime] = useState(new Date())

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000)
    return () => clearInterval(timer)
  }, [])

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="mt-1 text-sm text-gray-500">
            Monitor and manage your AI Platform services
          </p>
        </div>
        <div className="text-right">
          <p className="text-sm font-medium text-gray-900">
            {currentTime.toLocaleDateString('en-US', {
              weekday: 'long',
              year: 'numeric',
              month: 'long',
              day: 'numeric',
            })}
          </p>
          <p className="text-sm text-gray-500">
            {currentTime.toLocaleTimeString('en-US')}
          </p>
        </div>
      </div>

      {/* Summary stats */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Active Workflows"
          value="8"
          change="12%"
          changeType="increase"
          icon={CubeTransparentIcon}
        />
        <StatCard
          title="Models Deployed"
          value="12"
          change="3"
          changeType="increase"
          icon={CubeIcon}
        />
        <StatCard
          title="API Requests"
          value="45.2k"
          change="8%"
          changeType="increase"
          icon={ChartBarIcon}
        />
        <StatCard
          title="Avg Response Time"
          value="45ms"
          change="5%"
          changeType="decrease"
          icon={ClockIcon}
        />
      </div>

      {/* Module status cards */}
      <div>
        <h2 className="mb-4 text-lg font-semibold text-gray-900">
          System Modules
        </h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {moduleStatuses.map((module) => (
            <ModuleCard key={module.id} module={module} />
          ))}
        </div>
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Requests chart */}
        <div className="card p-6">
          <h3 className="mb-4 text-lg font-semibold text-gray-900">
            API Requests (24h)
          </h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={requestsData}>
                <defs>
                  <linearGradient id="colorRequests" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={CHART_COLORS.primary} stopOpacity={0.3} />
                    <stop offset="95%" stopColor={CHART_COLORS.primary} stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="time" stroke="#6b7280" fontSize={12} />
                <YAxis stroke="#6b7280" fontSize={12} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#fff',
                    border: '1px solid #e5e7eb',
                    borderRadius: '8px',
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="requests"
                  stroke={CHART_COLORS.primary}
                  fillOpacity={1}
                  fill="url(#colorRequests)"
                  strokeWidth={2}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Workflow stats chart */}
        <div className="card p-6">
          <h3 className="mb-4 text-lg font-semibold text-gray-900">
            Workflow Executions (7 days)
          </h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={workflowStats}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="name" stroke="#6b7280" fontSize={12} />
                <YAxis stroke="#6b7280" fontSize={12} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#fff',
                    border: '1px solid #e5e7eb',
                    borderRadius: '8px',
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="completed"
                  stroke={CHART_COLORS.success}
                  strokeWidth={2}
                  dot={{ fill: CHART_COLORS.success, strokeWidth: 2 }}
                />
                <Line
                  type="monotone"
                  dataKey="failed"
                  stroke={CHART_COLORS.danger}
                  strokeWidth={2}
                  dot={{ fill: CHART_COLORS.danger, strokeWidth: 2 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Quick actions and activity */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Quick actions */}
        <div className="card p-6">
          <h3 className="mb-4 text-lg font-semibold text-gray-900">
            Quick Actions
          </h3>
          <div className="grid grid-cols-2 gap-3">
            <QuickAction
              icon={PlusIcon}
              label="New Workflow"
              gradient="from-purple-500 to-purple-600"
              onClick={() => console.log('New workflow')}
            />
            <QuickAction
              icon={CloudArrowUpIcon}
              label="Deploy Model"
              gradient="from-pink-500 to-pink-600"
              onClick={() => console.log('Deploy model')}
            />
            <QuickAction
              icon={CpuChipIcon}
              label="Generate Code"
              gradient="from-green-500 to-green-600"
              onClick={() => console.log('Generate code')}
            />
            <QuickAction
              icon={ChartBarIcon}
              label="View Reports"
              gradient="from-blue-500 to-blue-600"
              onClick={() => console.log('View reports')}
            />
          </div>
        </div>

        {/* Recent activity */}
        <div className="card col-span-1 p-6 lg:col-span-2">
          <h3 className="mb-4 text-lg font-semibold text-gray-900">
            Recent Activity
          </h3>
          <div className="space-y-4">
            {recentActivity.map((activity) => (
              <div
                key={activity.id}
                className="flex items-start gap-3 rounded-lg p-3 transition-colors hover:bg-gray-50"
              >
                <div className={`mt-0.5 ${activity.iconColor}`}>
                  <activity.icon className="h-5 w-5" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-gray-900">{activity.message}</p>
                  <p className="text-xs text-gray-500">{activity.time}</p>
                </div>
              </div>
            ))}
          </div>
          <button className="mt-4 w-full rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50">
            View All Activity
          </button>
        </div>
      </div>

      {/* Resource usage */}
      <div className="card p-6">
        <h3 className="mb-4 text-lg font-semibold text-gray-900">
          Resource Usage
        </h3>
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {resourceUsageData.map((resource) => (
            <div key={resource.name} className="text-center">
              <div className="relative mx-auto h-32 w-32">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={[
                        { value: resource.value },
                        { value: 100 - resource.value },
                      ]}
                      cx="50%"
                      cy="50%"
                      innerRadius={35}
                      outerRadius={50}
                      startAngle={90}
                      endAngle={-270}
                      dataKey="value"
                    >
                      <Cell fill={resource.color} />
                      <Cell fill="#e5e7eb" />
                    </Pie>
                  </PieChart>
                </ResponsiveContainer>
                <div className="absolute inset-0 flex items-center justify-center">
                  <span className="text-xl font-bold text-gray-900">
                    {resource.value}%
                  </span>
                </div>
              </div>
              <p className="mt-2 font-medium text-gray-900">{resource.name}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Service Health */}
      <div className="card p-6">
        <h3 className="mb-4 text-lg font-semibold text-gray-900">
          Service Health
        </h3>
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6">
          {[
            { name: 'PostgreSQL', status: 'healthy' },
            { name: 'MongoDB', status: 'healthy' },
            { name: 'Redis', status: 'healthy' },
            { name: 'Kafka', status: 'warning' },
            { name: 'NGINX', status: 'healthy' },
            { name: 'Ray Cluster', status: 'healthy' },
          ].map((service) => (
            <div
              key={service.name}
              className="flex items-center gap-2 rounded-lg border border-gray-200 p-3"
            >
              {service.status === 'healthy' ? (
                <CheckCircleIcon className="h-5 w-5 text-green-500" />
              ) : service.status === 'warning' ? (
                <ExclamationTriangleIcon className="h-5 w-5 text-yellow-500" />
              ) : (
                <XCircleIcon className="h-5 w-5 text-red-500" />
              )}
              <span className="text-sm font-medium text-gray-700">
                {service.name}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default Dashboard
