"""
Tests for log capture functionality.

These tests verify that the LogCapture utility correctly captures
and formats failure information for email notifications.
"""

import logging
from utils.log_capture import LogCapture, LogCaptureHandler


def test_log_capture_basic():
    """Test basic log capture functionality."""
    log_capture = LogCapture()
    
    # Add some log entries
    log_capture.add_log("INFO", "Starting process")
    log_capture.add_log("WARNING", "Rate limit approaching")
    log_capture.add_log("ERROR", "Failed to connect to API")
    
    # Verify logs were captured
    assert len(log_capture.log_buffer) == 3
    assert log_capture.log_buffer[0]["level"] == "INFO"
    assert log_capture.log_buffer[2]["level"] == "ERROR"


def test_request_data_capture():
    """Test capturing request data."""
    log_capture = LogCapture()
    
    request_body = {"url": "https://www.youtube.com/watch?v=test"}
    headers = {
        "content-type": "application/json",
        "x-functions-key": "secret-key-123"
    }
    
    log_capture.set_request_data(request_body, headers)
    
    # Verify request data captured
    assert log_capture.request_data["body"]["url"] == "https://www.youtube.com/watch?v=test"
    
    # Verify sensitive header redacted
    assert log_capture.request_data["headers"]["x-functions-key"] == "[REDACTED]"
    assert log_capture.request_data["headers"]["content-type"] == "application/json"


def test_error_info_capture():
    """Test capturing error information."""
    log_capture = LogCapture()
    
    try:
        raise ValueError("Invalid input parameter")
    except ValueError as e:
        log_capture.set_error_info(e, {"parameter": "url", "value": "invalid"})
    
    # Verify error info captured
    assert log_capture.error_info["type"] == "ValueError"
    assert log_capture.error_info["message"] == "Invalid input parameter"
    assert "ValueError" in log_capture.error_info["traceback"]
    assert log_capture.error_info["context"]["parameter"] == "url"


def test_markdown_report_generation():
    """Test generating markdown failure report."""
    log_capture = LogCapture()
    
    # Simulate a request
    log_capture.set_request_data(
        {"url": "https://www.youtube.com/watch?v=test"},
        {"content-type": "application/json"}
    )
    
    # Add logs
    log_capture.add_log("INFO", "Processing request")
    log_capture.add_log("ERROR", "API call failed")
    
    # Capture error
    try:
        raise Exception("API timeout")
    except Exception as e:
        log_capture.set_error_info(e, {"api": "gemini"})
    
    # Generate report
    report = log_capture.generate_markdown_report()
    
    # Verify report structure
    assert "# Azure Functions Failure Report" in report
    assert "## Request Information" in report
    assert "## Error Information" in report
    assert "## Runtime Logs" in report
    assert "https://www.youtube.com/watch?v=test" in report
    assert "API timeout" in report
    assert "Processing request" in report


def test_log_capture_handler():
    """Test LogCaptureHandler integration with logging."""
    log_capture = LogCapture()
    handler = LogCaptureHandler(log_capture)
    
    # Create a logger with the capture handler
    logger = logging.getLogger("test_logger")
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    
    # Log some messages
    logger.info("Test info message")
    logger.warning("Test warning message")
    logger.error("Test error message")
    
    # Verify logs captured
    assert len(log_capture.log_buffer) >= 3
    
    # Clean up
    logger.removeHandler(handler)


if __name__ == "__main__":
    print("Running log capture tests...")
    test_log_capture_basic()
    print("✓ Basic log capture test passed")
    
    test_request_data_capture()
    print("✓ Request data capture test passed")
    
    test_error_info_capture()
    print("✓ Error info capture test passed")
    
    test_markdown_report_generation()
    print("✓ Markdown report generation test passed")
    
    test_log_capture_handler()
    print("✓ Log capture handler test passed")
    
    print("\nAll tests passed! ✅")
