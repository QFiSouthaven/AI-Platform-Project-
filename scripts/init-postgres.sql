-- =============================================================================
-- AI Platform - PostgreSQL Initialization Script
-- =============================================================================
-- This script runs automatically when the PostgreSQL container is first created
-- It sets up schemas and initial tables for the AI Platform modules
--
-- Modules using PostgreSQL:
--   - Module 1: User Gateway (users, sessions, api_keys)
--   - Module 2: Workflow Orchestration (workflows, tasks, executions)
-- =============================================================================

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- =============================================================================
-- Schema: user_gateway
-- Module 1: User Gateway tables
-- =============================================================================
CREATE SCHEMA IF NOT EXISTS user_gateway;

-- Users table
CREATE TABLE IF NOT EXISTS user_gateway.users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255),
    full_name VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    is_superuser BOOLEAN DEFAULT FALSE,
    oauth_provider VARCHAR(50),
    oauth_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- API Keys table
CREATE TABLE IF NOT EXISTS user_gateway.api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES user_gateway.users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    key_hash VARCHAR(255) NOT NULL,
    prefix VARCHAR(10) NOT NULL,
    scopes TEXT[] DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    last_used_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Sessions table
CREATE TABLE IF NOT EXISTS user_gateway.sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES user_gateway.users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL,
    refresh_token_hash VARCHAR(255),
    ip_address INET,
    user_agent TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for user_gateway
CREATE INDEX IF NOT EXISTS idx_users_email ON user_gateway.users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON user_gateway.users(username);
CREATE INDEX IF NOT EXISTS idx_api_keys_user_id ON user_gateway.api_keys(user_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_prefix ON user_gateway.api_keys(prefix);
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON user_gateway.sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_token_hash ON user_gateway.sessions(token_hash);

-- =============================================================================
-- Schema: workflow
-- Module 2: Workflow Orchestration tables
-- =============================================================================
CREATE SCHEMA IF NOT EXISTS workflow;

-- Workflow definitions
CREATE TABLE IF NOT EXISTS workflow.workflows (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    version INTEGER DEFAULT 1,
    status VARCHAR(50) DEFAULT 'draft',
    definition JSONB NOT NULL DEFAULT '{}',
    config JSONB DEFAULT '{}',
    tags TEXT[] DEFAULT '{}',
    created_by UUID,
    is_template BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Workflow executions
CREATE TABLE IF NOT EXISTS workflow.workflow_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workflow_id UUID NOT NULL REFERENCES workflow.workflows(id) ON DELETE CASCADE,
    status VARCHAR(50) DEFAULT 'pending',
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    input_data JSONB DEFAULT '{}',
    output_data JSONB DEFAULT '{}',
    error_message TEXT,
    metrics JSONB DEFAULT '{}',
    triggered_by UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Task definitions
CREATE TABLE IF NOT EXISTS workflow.tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workflow_id UUID NOT NULL REFERENCES workflow.workflows(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    task_type VARCHAR(100) NOT NULL,
    config JSONB DEFAULT '{}',
    dependencies UUID[] DEFAULT '{}',
    retry_policy JSONB DEFAULT '{"max_retries": 3, "backoff": "exponential"}',
    timeout_seconds INTEGER DEFAULT 3600,
    position INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Task executions
CREATE TABLE IF NOT EXISTS workflow.task_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID NOT NULL REFERENCES workflow.tasks(id) ON DELETE CASCADE,
    workflow_execution_id UUID NOT NULL REFERENCES workflow.workflow_executions(id) ON DELETE CASCADE,
    status VARCHAR(50) DEFAULT 'pending',
    attempt_number INTEGER DEFAULT 1,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    input_data JSONB DEFAULT '{}',
    output_data JSONB DEFAULT '{}',
    error_message TEXT,
    logs TEXT,
    worker_id VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for workflow
CREATE INDEX IF NOT EXISTS idx_workflows_name ON workflow.workflows(name);
CREATE INDEX IF NOT EXISTS idx_workflows_status ON workflow.workflows(status);
CREATE INDEX IF NOT EXISTS idx_workflows_created_by ON workflow.workflows(created_by);
CREATE INDEX IF NOT EXISTS idx_workflows_tags ON workflow.workflows USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_workflow_executions_workflow_id ON workflow.workflow_executions(workflow_id);
CREATE INDEX IF NOT EXISTS idx_workflow_executions_status ON workflow.workflow_executions(status);
CREATE INDEX IF NOT EXISTS idx_tasks_workflow_id ON workflow.tasks(workflow_id);
CREATE INDEX IF NOT EXISTS idx_task_executions_task_id ON workflow.task_executions(task_id);
CREATE INDEX IF NOT EXISTS idx_task_executions_workflow_execution_id ON workflow.task_executions(workflow_execution_id);
CREATE INDEX IF NOT EXISTS idx_task_executions_status ON workflow.task_executions(status);

-- =============================================================================
-- Functions and Triggers
-- =============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON user_gateway.users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_workflows_updated_at
    BEFORE UPDATE ON workflow.workflows
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tasks_updated_at
    BEFORE UPDATE ON workflow.tasks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- Initial Data (Optional)
-- =============================================================================

-- Create a system user for automated tasks
INSERT INTO user_gateway.users (id, email, username, full_name, is_active, is_verified, is_superuser)
VALUES (
    '00000000-0000-0000-0000-000000000000',
    'system@aiplatform.local',
    'system',
    'System User',
    TRUE,
    TRUE,
    TRUE
) ON CONFLICT (email) DO NOTHING;

-- Grant permissions
GRANT USAGE ON SCHEMA user_gateway TO PUBLIC;
GRANT USAGE ON SCHEMA workflow TO PUBLIC;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA user_gateway TO PUBLIC;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA workflow TO PUBLIC;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA user_gateway TO PUBLIC;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA workflow TO PUBLIC;

-- =============================================================================
-- Completion message
-- =============================================================================
DO $$
BEGIN
    RAISE NOTICE 'AI Platform PostgreSQL initialization completed successfully';
END $$;
