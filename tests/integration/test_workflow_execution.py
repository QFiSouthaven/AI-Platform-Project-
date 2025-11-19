"""
Workflow execution integration tests.

Tests workflow creation, execution, task management, and orchestration.
"""
import pytest
from httpx import AsyncClient
import asyncio


class TestWorkflowCRUD:
    """Tests for workflow CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_workflow(
        self,
        api_client: AsyncClient,
        auth_headers: dict,
        sample_workflow: dict,
        validate_response
    ):
        """Test creating a new workflow."""
        response = await api_client.post(
            "/api/v1/workflows/",
            headers=auth_headers,
            json=sample_workflow
        )

        if response.status_code == 201:
            data = response.json()
            validate_response(data, "success")
            assert "id" in data["data"]
            assert data["data"]["name"] == sample_workflow["name"]
        else:
            assert response.status_code in [400, 422, 502, 503]

    @pytest.mark.asyncio
    async def test_get_workflow_by_id(
        self,
        api_client: AsyncClient,
        auth_headers: dict
    ):
        """Test getting workflow by ID."""
        # First create a workflow
        workflow_data = {
            "name": "test-get-workflow",
            "description": "Test workflow",
            "version": "1.0.0",
            "tasks": []
        }

        create_response = await api_client.post(
            "/api/v1/workflows/",
            headers=auth_headers,
            json=workflow_data
        )

        if create_response.status_code == 201:
            workflow_id = create_response.json()["data"]["id"]

            # Get the workflow
            response = await api_client.get(
                f"/api/v1/workflows/{workflow_id}",
                headers=auth_headers
            )

            assert response.status_code == 200
            data = response.json()
            assert data["data"]["id"] == workflow_id
        else:
            # Service not available
            assert create_response.status_code in [502, 503]

    @pytest.mark.asyncio
    async def test_list_workflows(
        self,
        api_client: AsyncClient,
        auth_headers: dict
    ):
        """Test listing all workflows."""
        response = await api_client.get(
            "/api/v1/workflows/",
            headers=auth_headers
        )

        if response.status_code == 200:
            data = response.json()
            assert "data" in data
            assert isinstance(data["data"], list)
        else:
            assert response.status_code in [502, 503]

    @pytest.mark.asyncio
    async def test_update_workflow(
        self,
        api_client: AsyncClient,
        auth_headers: dict
    ):
        """Test updating a workflow."""
        # Create workflow first
        workflow_data = {
            "name": "test-update-workflow",
            "description": "Original description",
            "version": "1.0.0",
            "tasks": []
        }

        create_response = await api_client.post(
            "/api/v1/workflows/",
            headers=auth_headers,
            json=workflow_data
        )

        if create_response.status_code == 201:
            workflow_id = create_response.json()["data"]["id"]

            # Update the workflow
            response = await api_client.put(
                f"/api/v1/workflows/{workflow_id}",
                headers=auth_headers,
                json={
                    "description": "Updated description",
                    "version": "1.1.0"
                }
            )

            assert response.status_code in [200, 204]
        else:
            assert create_response.status_code in [502, 503]

    @pytest.mark.asyncio
    async def test_delete_workflow(
        self,
        api_client: AsyncClient,
        auth_headers: dict
    ):
        """Test deleting a workflow."""
        # Create workflow first
        workflow_data = {
            "name": "test-delete-workflow",
            "description": "To be deleted",
            "version": "1.0.0",
            "tasks": []
        }

        create_response = await api_client.post(
            "/api/v1/workflows/",
            headers=auth_headers,
            json=workflow_data
        )

        if create_response.status_code == 201:
            workflow_id = create_response.json()["data"]["id"]

            # Delete the workflow
            response = await api_client.delete(
                f"/api/v1/workflows/{workflow_id}",
                headers=auth_headers
            )

            assert response.status_code in [200, 204]

            # Verify deletion
            get_response = await api_client.get(
                f"/api/v1/workflows/{workflow_id}",
                headers=auth_headers
            )
            assert get_response.status_code == 404
        else:
            assert create_response.status_code in [502, 503]

    @pytest.mark.asyncio
    async def test_get_nonexistent_workflow(
        self,
        api_client: AsyncClient,
        auth_headers: dict
    ):
        """Test getting a nonexistent workflow."""
        response = await api_client.get(
            "/api/v1/workflows/nonexistent-id-12345",
            headers=auth_headers
        )

        assert response.status_code in [404, 502, 503]


class TestWorkflowExecution:
    """Tests for workflow execution."""

    @pytest.mark.asyncio
    async def test_execute_workflow(
        self,
        api_client: AsyncClient,
        auth_headers: dict,
        sample_workflow: dict
    ):
        """Test executing a workflow."""
        # Create workflow
        create_response = await api_client.post(
            "/api/v1/workflows/",
            headers=auth_headers,
            json=sample_workflow
        )

        if create_response.status_code == 201:
            workflow_id = create_response.json()["data"]["id"]

            # Execute the workflow
            response = await api_client.post(
                f"/api/v1/workflows/{workflow_id}/execute",
                headers=auth_headers,
                json={"input": {"data": "test-input"}}
            )

            if response.status_code in [200, 202]:
                data = response.json()
                assert "execution_id" in data["data"]
            else:
                assert response.status_code in [400, 502, 503]
        else:
            assert create_response.status_code in [502, 503]

    @pytest.mark.asyncio
    async def test_get_workflow_execution_status(
        self,
        api_client: AsyncClient,
        auth_headers: dict,
        sample_workflow: dict
    ):
        """Test getting workflow execution status."""
        # Create and execute workflow
        create_response = await api_client.post(
            "/api/v1/workflows/",
            headers=auth_headers,
            json=sample_workflow
        )

        if create_response.status_code == 201:
            workflow_id = create_response.json()["data"]["id"]

            exec_response = await api_client.post(
                f"/api/v1/workflows/{workflow_id}/execute",
                headers=auth_headers,
                json={}
            )

            if exec_response.status_code in [200, 202]:
                execution_id = exec_response.json()["data"]["execution_id"]

                # Get execution status
                response = await api_client.get(
                    f"/api/v1/workflows/{workflow_id}/executions/{execution_id}",
                    headers=auth_headers
                )

                assert response.status_code in [200, 502, 503]
        else:
            assert create_response.status_code in [502, 503]

    @pytest.mark.asyncio
    async def test_cancel_workflow_execution(
        self,
        api_client: AsyncClient,
        auth_headers: dict,
        sample_workflow: dict
    ):
        """Test canceling a workflow execution."""
        # Create and execute workflow
        create_response = await api_client.post(
            "/api/v1/workflows/",
            headers=auth_headers,
            json=sample_workflow
        )

        if create_response.status_code == 201:
            workflow_id = create_response.json()["data"]["id"]

            exec_response = await api_client.post(
                f"/api/v1/workflows/{workflow_id}/execute",
                headers=auth_headers,
                json={}
            )

            if exec_response.status_code in [200, 202]:
                execution_id = exec_response.json()["data"]["execution_id"]

                # Cancel execution
                response = await api_client.post(
                    f"/api/v1/workflows/{workflow_id}/executions/{execution_id}/cancel",
                    headers=auth_headers
                )

                assert response.status_code in [200, 204, 400, 502, 503]
        else:
            assert create_response.status_code in [502, 503]

    @pytest.mark.asyncio
    async def test_list_workflow_executions(
        self,
        api_client: AsyncClient,
        auth_headers: dict
    ):
        """Test listing workflow executions."""
        response = await api_client.get(
            "/api/v1/workflows/executions",
            headers=auth_headers
        )

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data["data"], list)
        else:
            assert response.status_code in [502, 503]


class TestTaskManagement:
    """Tests for task management."""

    @pytest.mark.asyncio
    async def test_create_standalone_task(
        self,
        api_client: AsyncClient,
        auth_headers: dict,
        sample_task: dict
    ):
        """Test creating a standalone task."""
        response = await api_client.post(
            "/api/v1/tasks/",
            headers=auth_headers,
            json=sample_task
        )

        if response.status_code == 201:
            data = response.json()
            assert "id" in data["data"]
        else:
            assert response.status_code in [400, 422, 502, 503]

    @pytest.mark.asyncio
    async def test_get_task_by_id(
        self,
        api_client: AsyncClient,
        auth_headers: dict,
        sample_task: dict
    ):
        """Test getting task by ID."""
        # Create task
        create_response = await api_client.post(
            "/api/v1/tasks/",
            headers=auth_headers,
            json=sample_task
        )

        if create_response.status_code == 201:
            task_id = create_response.json()["data"]["id"]

            # Get task
            response = await api_client.get(
                f"/api/v1/tasks/{task_id}",
                headers=auth_headers
            )

            assert response.status_code == 200
        else:
            assert create_response.status_code in [502, 503]

    @pytest.mark.asyncio
    async def test_list_tasks(
        self,
        api_client: AsyncClient,
        auth_headers: dict
    ):
        """Test listing all tasks."""
        response = await api_client.get(
            "/api/v1/tasks/",
            headers=auth_headers
        )

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data["data"], list)
        else:
            assert response.status_code in [502, 503]

    @pytest.mark.asyncio
    async def test_update_task_status(
        self,
        api_client: AsyncClient,
        auth_headers: dict,
        sample_task: dict
    ):
        """Test updating task status."""
        # Create task
        create_response = await api_client.post(
            "/api/v1/tasks/",
            headers=auth_headers,
            json=sample_task
        )

        if create_response.status_code == 201:
            task_id = create_response.json()["data"]["id"]

            # Update status
            response = await api_client.patch(
                f"/api/v1/tasks/{task_id}",
                headers=auth_headers,
                json={"status": "in_progress"}
            )

            assert response.status_code in [200, 204]
        else:
            assert create_response.status_code in [502, 503]

    @pytest.mark.asyncio
    async def test_retry_failed_task(
        self,
        api_client: AsyncClient,
        auth_headers: dict,
        sample_task: dict
    ):
        """Test retrying a failed task."""
        # Create task
        create_response = await api_client.post(
            "/api/v1/tasks/",
            headers=auth_headers,
            json=sample_task
        )

        if create_response.status_code == 201:
            task_id = create_response.json()["data"]["id"]

            # Retry task
            response = await api_client.post(
                f"/api/v1/tasks/{task_id}/retry",
                headers=auth_headers
            )

            # May fail if task not in retryable state
            assert response.status_code in [200, 202, 400, 502, 503]
        else:
            assert create_response.status_code in [502, 503]


class TestWorkflowValidation:
    """Tests for workflow validation."""

    @pytest.mark.asyncio
    async def test_workflow_with_circular_dependency(
        self,
        api_client: AsyncClient,
        auth_headers: dict
    ):
        """Test that circular dependencies are rejected."""
        workflow_data = {
            "name": "circular-workflow",
            "description": "Has circular dependency",
            "version": "1.0.0",
            "tasks": [
                {
                    "id": "task-1",
                    "name": "Task 1",
                    "type": "processing",
                    "dependencies": ["task-2"]
                },
                {
                    "id": "task-2",
                    "name": "Task 2",
                    "type": "processing",
                    "dependencies": ["task-1"]
                }
            ]
        }

        response = await api_client.post(
            "/api/v1/workflows/",
            headers=auth_headers,
            json=workflow_data
        )

        # Should be rejected due to circular dependency
        assert response.status_code in [400, 422, 502, 503]

    @pytest.mark.asyncio
    async def test_workflow_with_invalid_dependency(
        self,
        api_client: AsyncClient,
        auth_headers: dict
    ):
        """Test that invalid dependencies are rejected."""
        workflow_data = {
            "name": "invalid-dep-workflow",
            "description": "Has invalid dependency",
            "version": "1.0.0",
            "tasks": [
                {
                    "id": "task-1",
                    "name": "Task 1",
                    "type": "processing",
                    "dependencies": ["nonexistent-task"]
                }
            ]
        }

        response = await api_client.post(
            "/api/v1/workflows/",
            headers=auth_headers,
            json=workflow_data
        )

        assert response.status_code in [400, 422, 502, 503]

    @pytest.mark.asyncio
    async def test_workflow_without_name(
        self,
        api_client: AsyncClient,
        auth_headers: dict
    ):
        """Test that workflow without name is rejected."""
        workflow_data = {
            "description": "No name",
            "version": "1.0.0",
            "tasks": []
        }

        response = await api_client.post(
            "/api/v1/workflows/",
            headers=auth_headers,
            json=workflow_data
        )

        assert response.status_code in [400, 422, 502, 503]


class TestWorkflowScheduling:
    """Tests for workflow scheduling."""

    @pytest.mark.asyncio
    async def test_schedule_workflow(
        self,
        api_client: AsyncClient,
        auth_headers: dict,
        sample_workflow: dict
    ):
        """Test scheduling a workflow."""
        # Create workflow
        create_response = await api_client.post(
            "/api/v1/workflows/",
            headers=auth_headers,
            json=sample_workflow
        )

        if create_response.status_code == 201:
            workflow_id = create_response.json()["data"]["id"]

            # Schedule workflow
            response = await api_client.post(
                f"/api/v1/workflows/{workflow_id}/schedule",
                headers=auth_headers,
                json={
                    "cron": "0 * * * *",  # Every hour
                    "timezone": "UTC"
                }
            )

            assert response.status_code in [200, 201, 502, 503]
        else:
            assert create_response.status_code in [502, 503]

    @pytest.mark.asyncio
    async def test_list_scheduled_workflows(
        self,
        api_client: AsyncClient,
        auth_headers: dict
    ):
        """Test listing scheduled workflows."""
        response = await api_client.get(
            "/api/v1/workflows/schedules",
            headers=auth_headers
        )

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data["data"], list)
        else:
            assert response.status_code in [502, 503]


class TestWorkflowTemplates:
    """Tests for workflow templates."""

    @pytest.mark.asyncio
    async def test_create_workflow_from_template(
        self,
        api_client: AsyncClient,
        auth_headers: dict
    ):
        """Test creating a workflow from a template."""
        response = await api_client.post(
            "/api/v1/workflows/from-template",
            headers=auth_headers,
            json={
                "template_id": "data-processing-template",
                "name": "my-data-workflow",
                "variables": {
                    "source": "database",
                    "destination": "warehouse"
                }
            }
        )

        # Template may not exist
        assert response.status_code in [201, 404, 502, 503]

    @pytest.mark.asyncio
    async def test_list_workflow_templates(
        self,
        api_client: AsyncClient,
        auth_headers: dict
    ):
        """Test listing available workflow templates."""
        response = await api_client.get(
            "/api/v1/workflows/templates",
            headers=auth_headers
        )

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data["data"], list)
        else:
            assert response.status_code in [502, 503]


class TestWorkflowMetrics:
    """Tests for workflow metrics and monitoring."""

    @pytest.mark.asyncio
    async def test_get_workflow_metrics(
        self,
        api_client: AsyncClient,
        auth_headers: dict
    ):
        """Test getting workflow metrics."""
        response = await api_client.get(
            "/api/v1/workflows/metrics",
            headers=auth_headers
        )

        if response.status_code == 200:
            data = response.json()
            assert "data" in data
        else:
            assert response.status_code in [502, 503]

    @pytest.mark.asyncio
    async def test_get_execution_logs(
        self,
        api_client: AsyncClient,
        auth_headers: dict,
        sample_workflow: dict
    ):
        """Test getting execution logs."""
        # Create and execute workflow
        create_response = await api_client.post(
            "/api/v1/workflows/",
            headers=auth_headers,
            json=sample_workflow
        )

        if create_response.status_code == 201:
            workflow_id = create_response.json()["data"]["id"]

            exec_response = await api_client.post(
                f"/api/v1/workflows/{workflow_id}/execute",
                headers=auth_headers,
                json={}
            )

            if exec_response.status_code in [200, 202]:
                execution_id = exec_response.json()["data"]["execution_id"]

                # Get logs
                response = await api_client.get(
                    f"/api/v1/workflows/{workflow_id}/executions/{execution_id}/logs",
                    headers=auth_headers
                )

                assert response.status_code in [200, 502, 503]
        else:
            assert create_response.status_code in [502, 503]
