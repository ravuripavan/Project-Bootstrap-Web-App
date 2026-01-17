"""
Pytest configuration and shared fixtures for orchestrator tests.
"""
import pytest
import asyncio


@pytest.fixture(scope="session")
def event_loop():
    """
    Create an event loop for the test session.
    Required for pytest-asyncio to work properly.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_discovery_input():
    """Sample input data for Discovery mode tests."""
    return {
        "project_overview": "Build a modern web application for task management",
        "key_features": "User authentication, task boards, real-time collaboration",
        "constraints": "Must be scalable and secure",
        "target_users": "Small to medium-sized teams",
    }


@pytest.fixture
def sample_direct_input():
    """Sample input data for Direct mode tests."""
    return {
        "project_name": "TaskManager API",
        "project_type": "api",
        "language_stack": "python",
        "framework": "fastapi",
        "database": "postgresql",
        "include_repo": True,
        "include_ci": True,
        "include_jira": False,
        "vcs_provider": "github",
        "ci_provider": "github-actions",
    }


@pytest.fixture
def sample_healthcare_input():
    """Sample input with healthcare domain keywords."""
    return {
        "project_overview": "Patient management system for clinics",
        "key_features": "Electronic health records, appointment scheduling, HIPAA compliance",
        "constraints": "Must comply with HIPAA regulations",
    }


@pytest.fixture
def sample_ecommerce_input():
    """Sample input with ecommerce domain keywords."""
    return {
        "project_overview": "Online marketplace for handmade goods",
        "key_features": "Product catalog, shopping cart, payment processing, order tracking",
        "constraints": "PCI-DSS compliant payment handling",
    }


@pytest.fixture
def sample_ml_project_input():
    """Sample input for ML project."""
    return {
        "project_overview": "Machine learning model for image classification",
        "key_features": "Model training pipeline, inference API, model versioning",
        "constraints": "GPU support required",
        "project_type": "ml-project",
    }
