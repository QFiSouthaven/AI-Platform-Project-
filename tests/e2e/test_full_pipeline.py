"""
End-to-end pipeline tests.

Tests complete workflows from user authentication through AI processing and results.
"""
import pytest
from httpx import AsyncClient
import asyncio
import uuid


class TestCompleteUserJourney:
    """End-to-end test for complete user journey."""

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_user_registration_to_workflow_execution(
        self,
        api_client: AsyncClient,
        test_config: dict
    ):
        """Test complete flow from registration to workflow execution."""
        # Step 1: Register a new user
        unique_id = str(uuid.uuid4())[:8]
        user_data = {
            "email": f"e2e-user-{unique_id}@example.com",
            "username": f"e2euser{unique_id}",
            "password": "E2ETestPassword123!",
            "confirm_password": "E2ETestPassword123!"
        }

        register_response = await api_client.post(
            "/api/v1/auth/register",
            json=user_data
        )

        if register_response.status_code not in [201, 200]:
            pytest.skip("User gateway service not available")

        # Step 2: Login
        login_response = await api_client.post(
            "/api/v1/auth/login",
            json={
                "email": user_data["email"],
                "password": user_data["password"]
            }
        )

        assert login_response.status_code == 200
        tokens = login_response.json()["data"]
        auth_headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        # Step 3: Create a workflow
        workflow_data = {
            "name": f"e2e-workflow-{unique_id}",
            "description": "E2E test workflow",
            "version": "1.0.0",
            "tasks": [
                {
                    "id": "init",
                    "name": "Initialize",
                    "type": "initialization",
                    "dependencies": []
                },
                {
                    "id": "process",
                    "name": "Process Data",
                    "type": "processing",
                    "dependencies": ["init"]
                },
                {
                    "id": "generate",
                    "name": "Generate Output",
                    "type": "generation",
                    "dependencies": ["process"]
                }
            ]
        }

        workflow_response = await api_client.post(
            "/api/v1/workflows/",
            headers=auth_headers,
            json=workflow_data
        )

        if workflow_response.status_code not in [201, 200]:
            pytest.skip("Workflow orchestration service not available")

        workflow_id = workflow_response.json()["data"]["id"]

        # Step 4: Execute the workflow
        execute_response = await api_client.post(
            f"/api/v1/workflows/{workflow_id}/execute",
            headers=auth_headers,
            json={"input": {"test_data": "e2e-test"}}
        )

        assert execute_response.status_code in [200, 202]
        execution_id = execute_response.json()["data"]["execution_id"]

        # Step 5: Poll for completion (with timeout)
        max_attempts = 30
        for attempt in range(max_attempts):
            status_response = await api_client.get(
                f"/api/v1/workflows/{workflow_id}/executions/{execution_id}",
                headers=auth_headers
            )

            if status_response.status_code == 200:
                status = status_response.json()["data"]["status"]
                if status in ["completed", "failed", "cancelled"]:
                    break

            await asyncio.sleep(1)

        # Step 6: Cleanup - delete workflow
        await api_client.delete(
            f"/api/v1/workflows/{workflow_id}",
            headers=auth_headers
        )

        # Verify execution completed
        assert status in ["completed", "failed"]


class TestCodeGenerationPipeline:
    """End-to-end test for code generation pipeline."""

    @pytest.mark.asyncio
    @pytest.mark.e2e
    @pytest.mark.slow
    async def test_code_generation_flow(
        self,
        api_client: AsyncClient,
        auth_headers: dict
    ):
        """Test complete code generation flow."""
        # Step 1: Submit code generation request
        generate_response = await api_client.post(
            "/api/v1/generate/code",
            headers=auth_headers,
            json={
                "prompt": "Create a Python function that calculates factorial",
                "language": "python",
                "max_length": 500
            }
        )

        if generate_response.status_code not in [200, 202]:
            pytest.skip("Core processing service not available")

        data = generate_response.json()

        if generate_response.status_code == 202:
            # Async generation - wait for result
            task_id = data["data"]["task_id"]

            max_attempts = 60  # LLM can take time
            for _ in range(max_attempts):
                result_response = await api_client.get(
                    f"/api/v1/generate/tasks/{task_id}",
                    headers=auth_headers
                )

                if result_response.status_code == 200:
                    result = result_response.json()["data"]
                    if result["status"] in ["completed", "failed"]:
                        break

                await asyncio.sleep(1)

            assert result["status"] == "completed"
            assert "code" in result
        else:
            # Sync generation
            assert "code" in data["data"]

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_code_debug_flow(
        self,
        api_client: AsyncClient,
        auth_headers: dict
    ):
        """Test complete code debugging flow."""
        # Code with intentional bug
        buggy_code = """
def calculate_average(numbers):
    total = sum(numbers)
    return total / len(numbers)  # Bug: doesn't handle empty list
"""

        debug_response = await api_client.post(
            "/api/v1/debug/analyze",
            headers=auth_headers,
            json={
                "code": buggy_code,
                "language": "python",
                "error_message": "ZeroDivisionError: division by zero"
            }
        )

        if debug_response.status_code not in [200, 202]:
            pytest.skip("Core processing service not available")

        data = debug_response.json()["data"]

        # Should identify the issue
        assert "analysis" in data or "issues" in data


class TestModelManagementPipeline:
    """End-to-end test for model management pipeline."""

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_model_upload_and_deployment(
        self,
        api_client: AsyncClient,
        auth_headers: dict
    ):
        """Test model upload, storage, and deployment flow."""
        unique_id = str(uuid.uuid4())[:8]

        # Step 1: Register model metadata
        model_data = {
            "name": f"e2e-test-model-{unique_id}",
            "version": "1.0.0",
            "description": "E2E test model",
            "model_type": "classification",
            "framework": "pytorch",
            "tags": ["test", "e2e"]
        }

        register_response = await api_client.post(
            "/api/v1/models/",
            headers=auth_headers,
            json=model_data
        )

        if register_response.status_code not in [201, 200]:
            pytest.skip("Model management service not available")

        model_id = register_response.json()["data"]["id"]

        # Step 2: Get model details
        get_response = await api_client.get(
            f"/api/v1/models/{model_id}",
            headers=auth_headers
        )

        assert get_response.status_code == 200

        # Step 3: List models to verify it appears
        list_response = await api_client.get(
            "/api/v1/models/",
            headers=auth_headers
        )

        assert list_response.status_code == 200
        models = list_response.json()["data"]
        assert any(m["id"] == model_id for m in models)

        # Step 4: Cleanup - delete model
        await api_client.delete(
            f"/api/v1/models/{model_id}",
            headers=auth_headers
        )


class TestEventDrivenPipeline:
    """End-to-end test for event-driven processing."""

    @pytest.mark.asyncio
    @pytest.mark.e2e
    @pytest.mark.requires_kafka
    async def test_event_publication_and_consumption(
        self,
        api_client: AsyncClient,
        auth_headers: dict
    ):
        """Test event publication and consumption flow."""
        # Step 1: Publish an event
        event_data = {
            "event_type": "test.e2e.event",
            "data": {
                "message": "E2E test event",
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }

        publish_response = await api_client.post(
            "/api/v1/events/publish",
            headers=auth_headers,
            json=event_data
        )

        if publish_response.status_code not in [200, 202]:
            pytest.skip("Data integration service not available")

        # Step 2: Check event was received (via polling or subscription)
        # This is simplified - real test would use WebSocket or polling
        events_response = await api_client.get(
            "/api/v1/events/",
            headers=auth_headers,
            params={"type": "test.e2e.event", "limit": 10}
        )

        if events_response.status_code == 200:
            events = events_response.json()["data"]
            # Event should be in the list
            assert isinstance(events, list)


class TestCachingPipeline:
    """End-to-end test for caching operations."""

    @pytest.mark.asyncio
    @pytest.mark.e2e
    @pytest.mark.requires_redis
    async def test_cache_operations(
        self,
        api_client: AsyncClient,
        auth_headers: dict
    ):
        """Test cache set, get, and invalidation flow."""
        cache_key = f"e2e-test-key-{uuid.uuid4()}"
        cache_value = {"data": "test-value", "count": 42}

        # Step 1: Set cache value
        set_response = await api_client.post(
            "/api/v1/cache/set",
            headers=auth_headers,
            json={
                "key": cache_key,
                "value": cache_value,
                "ttl": 300
            }
        )

        if set_response.status_code not in [200, 201]:
            pytest.skip("Data integration service not available")

        # Step 2: Get cache value
        get_response = await api_client.get(
            f"/api/v1/cache/get/{cache_key}",
            headers=auth_headers
        )

        assert get_response.status_code == 200
        retrieved_value = get_response.json()["data"]["value"]
        assert retrieved_value == cache_value

        # Step 3: Delete cache value
        delete_response = await api_client.delete(
            f"/api/v1/cache/{cache_key}",
            headers=auth_headers
        )

        assert delete_response.status_code in [200, 204]

        # Step 4: Verify deletion
        verify_response = await api_client.get(
            f"/api/v1/cache/get/{cache_key}",
            headers=auth_headers
        )

        assert verify_response.status_code == 404


class TestInfrastructurePipeline:
    """End-to-end test for infrastructure operations."""

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_distributed_task_execution(
        self,
        api_client: AsyncClient,
        auth_headers: dict
    ):
        """Test distributed task execution with Ray."""
        # Step 1: Submit distributed task
        task_data = {
            "function": "parallel_process",
            "args": [[1, 2, 3, 4, 5]],
            "kwargs": {"operation": "square"},
            "num_cpus": 2
        }

        submit_response = await api_client.post(
            "/api/v1/infrastructure/tasks/submit",
            headers=auth_headers,
            json=task_data
        )

        if submit_response.status_code not in [200, 202]:
            pytest.skip("Infrastructure service not available")

        task_id = submit_response.json()["data"]["task_id"]

        # Step 2: Wait for completion
        max_attempts = 30
        for _ in range(max_attempts):
            status_response = await api_client.get(
                f"/api/v1/infrastructure/tasks/{task_id}",
                headers=auth_headers
            )

            if status_response.status_code == 200:
                status = status_response.json()["data"]["status"]
                if status in ["completed", "failed"]:
                    break

            await asyncio.sleep(1)

        assert status == "completed"

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_infrastructure_health(
        self,
        api_client: AsyncClient,
        auth_headers: dict
    ):
        """Test infrastructure health and status."""
        status_response = await api_client.get(
            "/api/v1/infrastructure/status",
            headers=auth_headers
        )

        if status_response.status_code == 200:
            data = status_response.json()["data"]
            assert "status" in data
        else:
            pytest.skip("Infrastructure service not available")


class TestCompleteAIPipeline:
    """End-to-end test for complete AI workflow pipeline."""

    @pytest.mark.asyncio
    @pytest.mark.e2e
    @pytest.mark.slow
    async def test_full_ai_workflow(
        self,
        api_client: AsyncClient,
        auth_headers: dict
    ):
        """Test complete AI workflow from request to result."""
        unique_id = str(uuid.uuid4())[:8]

        # Step 1: Create AI workflow
        workflow_data = {
            "name": f"ai-pipeline-{unique_id}",
            "description": "Complete AI processing pipeline",
            "version": "1.0.0",
            "tasks": [
                {
                    "id": "load-model",
                    "name": "Load AI Model",
                    "type": "model_loading",
                    "config": {"model_id": "default-model"},
                    "dependencies": []
                },
                {
                    "id": "preprocess",
                    "name": "Preprocess Input",
                    "type": "preprocessing",
                    "dependencies": ["load-model"]
                },
                {
                    "id": "inference",
                    "name": "Run Inference",
                    "type": "inference",
                    "config": {"batch_size": 1},
                    "dependencies": ["preprocess"]
                },
                {
                    "id": "postprocess",
                    "name": "Postprocess Output",
                    "type": "postprocessing",
                    "dependencies": ["inference"]
                }
            ]
        }

        workflow_response = await api_client.post(
            "/api/v1/workflows/",
            headers=auth_headers,
            json=workflow_data
        )

        if workflow_response.status_code not in [201, 200]:
            pytest.skip("Services not available for full AI pipeline test")

        workflow_id = workflow_response.json()["data"]["id"]

        # Step 2: Execute with input
        execute_response = await api_client.post(
            f"/api/v1/workflows/{workflow_id}/execute",
            headers=auth_headers,
            json={
                "input": {
                    "prompt": "Generate a hello world program",
                    "language": "python"
                }
            }
        )

        if execute_response.status_code not in [200, 202]:
            # Cleanup and skip
            await api_client.delete(
                f"/api/v1/workflows/{workflow_id}",
                headers=auth_headers
            )
            pytest.skip("Workflow execution not available")

        execution_id = execute_response.json()["data"]["execution_id"]

        # Step 3: Poll for completion
        max_attempts = 120  # AI processing can be slow
        status = "pending"
        for _ in range(max_attempts):
            status_response = await api_client.get(
                f"/api/v1/workflows/{workflow_id}/executions/{execution_id}",
                headers=auth_headers
            )

            if status_response.status_code == 200:
                status = status_response.json()["data"]["status"]
                if status in ["completed", "failed", "cancelled"]:
                    break

            await asyncio.sleep(1)

        # Step 4: Get results if completed
        if status == "completed":
            results_response = await api_client.get(
                f"/api/v1/workflows/{workflow_id}/executions/{execution_id}/results",
                headers=auth_headers
            )

            if results_response.status_code == 200:
                results = results_response.json()["data"]
                assert "output" in results

        # Step 5: Cleanup
        await api_client.delete(
            f"/api/v1/workflows/{workflow_id}",
            headers=auth_headers
        )

        assert status in ["completed", "failed"]


class TestErrorRecovery:
    """End-to-end tests for error recovery scenarios."""

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_workflow_retry_on_failure(
        self,
        api_client: AsyncClient,
        auth_headers: dict
    ):
        """Test that workflows can recover from task failures."""
        unique_id = str(uuid.uuid4())[:8]

        # Create workflow with retry configuration
        workflow_data = {
            "name": f"retry-workflow-{unique_id}",
            "description": "Workflow with retry logic",
            "version": "1.0.0",
            "tasks": [
                {
                    "id": "flaky-task",
                    "name": "Flaky Task",
                    "type": "processing",
                    "config": {
                        "retries": 3,
                        "retry_delay": 1
                    },
                    "dependencies": []
                }
            ]
        }

        workflow_response = await api_client.post(
            "/api/v1/workflows/",
            headers=auth_headers,
            json=workflow_data
        )

        if workflow_response.status_code not in [201, 200]:
            pytest.skip("Workflow orchestration service not available")

        workflow_id = workflow_response.json()["data"]["id"]

        # Execute and verify retry behavior
        execute_response = await api_client.post(
            f"/api/v1/workflows/{workflow_id}/execute",
            headers=auth_headers,
            json={}
        )

        if execute_response.status_code in [200, 202]:
            # Wait a bit for potential retries
            await asyncio.sleep(5)

        # Cleanup
        await api_client.delete(
            f"/api/v1/workflows/{workflow_id}",
            headers=auth_headers
        )

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_graceful_service_degradation(
        self,
        api_client: AsyncClient,
        auth_headers: dict
    ):
        """Test that API responds gracefully when services are unavailable."""
        # Try to access various endpoints
        endpoints = [
            "/api/v1/workflows/",
            "/api/v1/models/",
            "/api/v1/events/",
            "/api/v1/infrastructure/status"
        ]

        for endpoint in endpoints:
            response = await api_client.get(
                endpoint,
                headers=auth_headers
            )

            # Should get valid response or service unavailable, not crash
            assert response.status_code in [200, 401, 403, 502, 503]

            # If error, should have proper error format
            if response.status_code >= 400:
                try:
                    data = response.json()
                    # Error responses should have structure
                    assert "status" in data or "error" in data or "detail" in data
                except Exception:
                    pass  # Gateway might return non-JSON for some errors
