import { Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'

// Placeholder pages for other modules
const UserGateway = () => (
  <div className="p-6">
    <h1 className="text-2xl font-bold text-gray-900">User Gateway</h1>
    <p className="mt-2 text-gray-600">Manage authentication, API keys, and user sessions.</p>
  </div>
)

const WorkflowOrchestration = () => (
  <div className="p-6">
    <h1 className="text-2xl font-bold text-gray-900">Workflow Orchestration</h1>
    <p className="mt-2 text-gray-600">Design, schedule, and monitor AI workflows.</p>
  </div>
)

const CoreProcessing = () => (
  <div className="p-6">
    <h1 className="text-2xl font-bold text-gray-900">Core Processing</h1>
    <p className="mt-2 text-gray-600">AI-powered code generation and processing.</p>
  </div>
)

const DataIntegration = () => (
  <div className="p-6">
    <h1 className="text-2xl font-bold text-gray-900">Data Integration</h1>
    <p className="mt-2 text-gray-600">Event streaming, caching, and data pipelines.</p>
  </div>
)

const ModelManagement = () => (
  <div className="p-6">
    <h1 className="text-2xl font-bold text-gray-900">Model Management</h1>
    <p className="mt-2 text-gray-600">Store, version, and deploy AI models.</p>
  </div>
)

const Infrastructure = () => (
  <div className="p-6">
    <h1 className="text-2xl font-bold text-gray-900">Infrastructure</h1>
    <p className="mt-2 text-gray-600">Parallel processing and resource management.</p>
  </div>
)

const Settings = () => (
  <div className="p-6">
    <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
    <p className="mt-2 text-gray-600">Configure platform settings and preferences.</p>
  </div>
)

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="gateway" element={<UserGateway />} />
        <Route path="workflows" element={<WorkflowOrchestration />} />
        <Route path="processing" element={<CoreProcessing />} />
        <Route path="data" element={<DataIntegration />} />
        <Route path="models" element={<ModelManagement />} />
        <Route path="infrastructure" element={<Infrastructure />} />
        <Route path="settings" element={<Settings />} />
      </Route>
    </Routes>
  )
}

export default App
