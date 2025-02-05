import pytest
import os
import tempfile


@pytest.fixture
def sample_html():
    return """
    <html>
        <head><title>Test Page</title></head>
        <body>
            <div class="content">
                <h1>Test Header</h1>
                <a href="/test-link" title="Test Link">Link Text</a>
                <img src="/test-image.jpg" alt="Test Image" title="Image Title">
            </div>
        </body>
    </html>
    """


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield tmpdirname


@pytest.fixture
def sample_metadata():
    return {
        "id": "12345",
        "title": "Test Title",
        "description": "Test Description",
        "url": "https://example.com/test"
    }
