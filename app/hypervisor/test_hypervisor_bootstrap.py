import pytest
import os
import logging
import tempfile
from unittest.mock import Mock, patch

# Import the functions to test (adjust import path as needed)
from bootstrap import (
    configure_logging,
    is_setup
)

class TestConfigureLogging:
    @pytest.fixture
    def temp_dir(self):
        with tempfile.TemporaryDirectory() as td:
            yield td

    def test_logger_basic_config(self, temp_dir):
        logger = configure_logging(temp_dir, verbose=False)
        
        assert logger.level == logging.DEBUG
        assert not logger.propagate
        assert len(logger.handlers) == 2
        
        logger.handlers.clear()

    def test_file_handler_setup(self, temp_dir):
        logger = configure_logging(temp_dir, verbose=False)
        
        file_handler = logger.handlers[0]
        assert isinstance(file_handler, logging.FileHandler)
        assert file_handler.level == logging.DEBUG
        assert os.path.exists(os.path.join(temp_dir, "bootstrap.log"))
        
        logger.handlers.clear()

    def test_console_handler_not_verbose(self, temp_dir):
        logger = configure_logging(temp_dir, verbose=False)
        
        console_handler = logger.handlers[1]
        assert isinstance(console_handler, logging.StreamHandler)
        assert console_handler.level == logging.WARNING
        
        logger.handlers.clear()

    def test_console_handler_verbose(self, temp_dir):
        logger = configure_logging(temp_dir, verbose=True)
        
        console_handler = logger.handlers[1]
        assert console_handler.level == logging.INFO
        
        logger.handlers.clear()

    def test_log_file_writing(self, temp_dir):
        logger = configure_logging(temp_dir, verbose=False)
        
        logger.info("test info message")
        logger.warning("test warning message")
        
        log_path = os.path.join(temp_dir, "bootstrap.log")
        with open(log_path) as f:
            content = f.read()
            assert "test info message" in content
            assert "test warning message" in content
        
        logger.handlers.clear()

    def test_formatter_applied(self, temp_dir):
        logger = configure_logging(temp_dir, verbose=False)
        
        for handler in logger.handlers:
            assert handler.formatter is not None
            assert "%(asctime)s - %(levelname)s - %(message)s" in handler.formatter._fmt
        
        logger.handlers.clear()

    @patch('sys.stderr')
    def test_stderr_output(self, mock_stderr, temp_dir):
        logger = configure_logging(temp_dir, verbose=True)
        
        logger.info("test stderr")
        logger.warning("test warning stderr")
        
        logger.handlers.clear()

    def test_log_file_overwrite_mode(self, temp_dir):
        log_path = os.path.join(temp_dir, "bootstrap.log")
        
        # Create initial log
        logger1 = configure_logging(temp_dir, verbose=False)
        logger1.info("first message")
        logger1.handlers.clear()
        
        # Create second logger - should overwrite
        logger2 = configure_logging(temp_dir, verbose=False)
        logger2.info("second message")
        
        with open(log_path) as f:
            content = f.read()
            assert "first message" not in content
            assert "second message" in content
        
        logger2.handlers.clear()

    def test_multiple_log_levels(self, temp_dir):
        logger = configure_logging(temp_dir, verbose=True)
        
        logger.debug("debug msg")
        logger.info("info msg")
        logger.warning("warning msg")
        logger.error("error msg")
        
        log_path = os.path.join(temp_dir, "bootstrap.log")
        with open(log_path) as f:
            content = f.read()
            assert all(msg in content for msg in ["debug msg", "info msg", "warning msg", "error msg"])
        
        logger.handlers.clear()


class TestIsSetup:
    @pytest.fixture
    def temp_dir(self):
        with tempfile.TemporaryDirectory() as td:
            yield td

    def test_both_files_exist(self, temp_dir):
        os.makedirs(os.path.join(temp_dir, "data"))
        open(os.path.join(temp_dir, "data", "config.json"), 'w').close()
        
        with patch('os.path.isfile') as mock_isfile:
            mock_isfile.side_effect = lambda path: (
                path == os.path.join(temp_dir, "data", "config.json") or
                path == "hypervisor_server.py"
            )
            assert is_setup(temp_dir) is True

    def test_missing_config(self, temp_dir):
        with patch('os.path.isfile') as mock_isfile:
            mock_isfile.side_effect = lambda path: path == "hypervisor_server.py"
            assert is_setup(temp_dir) is False

    def test_missing_hypervisor(self, temp_dir):
        os.makedirs(os.path.join(temp_dir, "data"))
        
        with patch('os.path.isfile') as mock_isfile:
            mock_isfile.side_effect = lambda path: path == os.path.join(temp_dir, "data", "config.json")
            assert is_setup(temp_dir) is False

    def test_both_missing(self, temp_dir):
        with patch('os.path.isfile', return_value=False):
            assert is_setup(temp_dir) is False

    def test_hypervisor_path_absolute(self, temp_dir):
        """Test that hypervisor_server.py is checked in current dir, not app_dir"""
        os.makedirs(os.path.join(temp_dir, "data"))
        
        with patch('os.path.isfile') as mock_isfile:
            mock_isfile.side_effect = lambda path: (
                path == os.path.join(temp_dir, "data", "config.json") or
                path == "hypervisor_server.py"
            )
            is_setup(temp_dir)
            
            # Verify hypervisor_server.py checked without app_dir prefix
            calls = [call[0][0] for call in mock_isfile.call_args_list]
            assert "hypervisor_server.py" in calls
            assert os.path.join(temp_dir, "hypervisor_server.py") not in calls

if __name__ == "__main__":
    pytest.main([__file__])