import os
import psutil
import subprocess
import logging
import coloredlogs
import sys
from typing import Optional, Dict, List


class OllamaManager:
    """
    Manages the lifecycle of the Ollama server process.
    This includes starting, stopping, and checking the status of the
    Ollama 'ollama serve' process using a PID file for tracking.
    Enhanced with comprehensive process detection and management.
    """

    def __init__(self, pid_file: Optional[str] = None, log_level: int = logging.INFO):
        """
        Initializes the OllamaManager.

        Args:
            pid_file (Optional[str]): The path to the file where the Ollama
                                      process ID (PID) will be stored.
                                      If None, some operations (like checking/stopping)
                                      will be limited or skipped.
            log_level (int): The logging verbosity level (e.g., logging.INFO,
                             logging.DEBUG). Defaults to logging.INFO.
        """
        self.pid_file = pid_file
        # Use a dedicated instance logger, which can be configured independently
        # if needed, but defaults to the module-level configuration.
        self.logger = self._setup_logger(log_level)
        self.logger.debug(f"OllamaManager initialized with PID file: {self.pid_file}")

    @staticmethod
    def _setup_logger(log_level: int) -> logging.Logger:
        """
        Configures and returns a logger instance for OllamaManager.
        This static method ensures that coloredlogs is installed and applied
        to the logger if it hasn't been already.

        Args:
            log_level (int): The desired logging level.

        Returns:
            logging.Logger: The configured logger instance.
        """
        logger = logging.getLogger("OllamaManager")  # Use a consistent name for this manager's logs
        logger.setLevel(log_level)

        # Check if handlers are already configured to prevent duplicate logs
        if not logger.handlers:
            # Apply coloredlogs for better console output
            fmt = "%(asctime)s [%(levelname)s] %(message)s"
            coloredlogs.install(level=log_level, logger=logger, fmt=fmt)
            logger.debug("Coloredlogs installed for OllamaManager logger.")
        return logger

    def find_ollama_processes(self) -> List[Dict]:
        """
        Find all processes that might be Ollama-related.

        Returns:
            List[Dict]: List of dictionaries containing process information
        """
        ollama_processes = []

        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'status']):
            try:
                # Check process name and command line for ollama
                name = proc.info['name'].lower()
                cmdline = ' '.join(proc.info['cmdline']).lower() if proc.info['cmdline'] else ''

                if 'ollama' in name or 'ollama' in cmdline:
                    ollama_processes.append({
                        'pid': proc.info['pid'],
                        'name': proc.info['name'],
                        'cmdline': proc.info['cmdline'],
                        'status': proc.info['status'],
                        'is_serve': 'serve' in cmdline
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        return ollama_processes

    def check_ollama_service(self) -> Optional[str]:
        """
        Check if ollama is running as a system service (macOS/Linux).

        Returns:
            Optional[str]: Service status description if found, None otherwise
        """
        try:
            # Check if running via launchctl (macOS)
            if sys.platform == 'darwin':
                result = subprocess.run(['launchctl', 'list'],
                                        capture_output=True, text=True, check=False)
                if 'ollama' in result.stdout.lower():
                    return "Running as macOS service (launchctl)"

            # Check if running via systemctl (Linux)
            elif sys.platform.startswith('linux'):
                result = subprocess.run(['systemctl', 'is-active', 'ollama'],
                                        capture_output=True, text=True, check=False)
                if result.returncode == 0:
                    return "Running as systemd service"
        except FileNotFoundError:
            pass

        return None

    def diagnose_ollama_status(self) -> Dict:
        """
        Comprehensive diagnostic of all Ollama processes and service status.

        Returns:
            Dict: Complete status information including processes, services, and recommendations
        """
        diagnosis = {
            'processes': [],
            'service_status': None,
            'pid_file_status': 'unknown',
            'recommendations': [],
            'total_processes': 0,
            'serve_processes': 0
        }

        # Find all Ollama processes
        processes = self.find_ollama_processes()
        diagnosis['processes'] = processes
        diagnosis['total_processes'] = len(processes)
        diagnosis['serve_processes'] = len([p for p in processes if p['is_serve']])

        # Check system services
        diagnosis['service_status'] = self.check_ollama_service()

        # Check PID file status
        if not self.pid_file:
            diagnosis['pid_file_status'] = 'not_configured'
            diagnosis['recommendations'].append("Configure PID file path for better tracking")
        elif not os.path.exists(self.pid_file):
            diagnosis['pid_file_status'] = 'missing'
            if processes:
                diagnosis['recommendations'].append(
                    "PID file missing but Ollama processes found - they weren't started by this manager")
        else:
            try:
                with open(self.pid_file, "r") as f:
                    stored_pid = int(f.read().strip())

                # Check if stored PID matches any running process
                matching_process = any(p['pid'] == stored_pid for p in processes)

                if matching_process:
                    diagnosis['pid_file_status'] = 'valid'
                else:
                    diagnosis['pid_file_status'] = 'stale'
                    diagnosis['recommendations'].append(f"PID file contains stale PID {stored_pid}")

            except (ValueError, FileNotFoundError) as e:
                diagnosis['pid_file_status'] = 'invalid'
                diagnosis['recommendations'].append(f"PID file is invalid: {e}")

        # Generate recommendations
        if not processes:
            diagnosis['recommendations'].append("No Ollama processes running - safe to start")
        elif diagnosis['serve_processes'] == 0:
            diagnosis['recommendations'].append(
                "Ollama processes found but no 'serve' processes - may need to start server")
        elif diagnosis['serve_processes'] > 1:
            diagnosis['recommendations'].append(
                f"Multiple 'serve' processes found ({diagnosis['serve_processes']}) - consider stopping duplicates")

        return diagnosis

    def print_diagnosis(self) -> None:
        """Print a comprehensive diagnosis of Ollama status."""
        diagnosis = self.diagnose_ollama_status()

        print("=== Ollama Process Diagnostics ===\n")

        # Process information
        if diagnosis['processes']:
            print(f"Found {diagnosis['total_processes']} Ollama-related process(es):")
            for proc in diagnosis['processes']:
                print(f"  PID: {proc['pid']}")
                print(f"  Name: {proc['name']}")
                print(f"  Status: {proc['status']}")
                print(f"  Command: {' '.join(proc['cmdline']) if proc['cmdline'] else 'N/A'}")
                print(f"  Is Serve: {'Yes' if proc['is_serve'] else 'No'}")
                print()
        else:
            print("No Ollama processes found in process list.")

        # Service status
        if diagnosis['service_status']:
            print(f"Service Status: {diagnosis['service_status']}")
        else:
            print("Not running as a system service.")

        # PID file status
        print(f"PID File Status: {diagnosis['pid_file_status']}")
        if self.pid_file:
            print(f"PID File Path: {self.pid_file}")

        # Recommendations
        if diagnosis['recommendations']:
            print("\n=== Recommendations ===")
            for i, rec in enumerate(diagnosis['recommendations'], 1):
                print(f"{i}. {rec}")

        print()

    def check_ollama_comprehensive(self) -> Dict:
        """
        Comprehensive check for Ollama processes, regardless of PID file status.

        Returns:
            Dict: {
                'status': int,  # 0 if any ollama found, -1 if none
                'processes': list,  # List of found ollama processes
                'pid_file_status': str,  # Status of the PID file tracking
                'recommendations': list  # What to do next
            }
        """
        diagnosis = self.diagnose_ollama_status()

        result = {
            'status': 0 if diagnosis['total_processes'] > 0 else -1,
            'processes': diagnosis['processes'],
            'pid_file_status': diagnosis['pid_file_status'],
            'recommendations': diagnosis['recommendations']
        }

        if diagnosis['total_processes'] > 0:
            if diagnosis['serve_processes'] > 0:
                self.logger.info(f"Found {diagnosis['serve_processes']} Ollama serve process(es)")
            else:
                self.logger.warning("Found Ollama processes but none appear to be 'ollama serve'")
        else:
            self.logger.info("No Ollama processes found")

        return result

    def check_ollama(self) -> int:
        """
        Checks if the Ollama server process is currently running.

        Reads the PID from the configured PID file and verifies if a process
        with that PID exists and is named "ollama".

        Returns:
            int:
                0: Ollama is running.
                -1: PID file path is not set (self.pid_file is None or empty).
                -2: PID file does not exist.
                -3: Process found, but its name is not "ollama" or it's not running.
                -4: Error reading PID file or accessing process (e.g., permission denied).
        """
        if not self.pid_file:
            self.logger.warning("PID file path is not configured. Cannot check Ollama status definitively.")
            return -1
        elif not os.path.exists(self.pid_file):
            self.logger.info(f"PID file '{self.pid_file}' does not exist. Ollama is likely not running.")
            return -2

        try:
            with open(self.pid_file, "r") as f:
                pid_str = f.read().strip()
                if not pid_str:
                    self.logger.warning(f"PID file '{self.pid_file}' is empty. Ollama is likely not running.")
                    return -4  # Treat as an error in PID file content
                pid = int(pid_str)

            # Check if the process exists and is indeed Ollama
            proc = psutil.Process(pid)
            # Check for "ollama" in the process name (case-insensitive)
            # and ensure the process is still running.
            if "ollama" in proc.name().lower() and proc.is_running():
                self.logger.info(f"Ollama is running with PID: {pid}.")
                return 0
            else:
                self.logger.warning(f"Process with PID {pid} found, but it's not the Ollama server "
                                    f"('{proc.name()}' instead of 'ollama') or it's not running.")
                return -3
        except psutil.NoSuchProcess:
            self.logger.info(f"No process found with PID from '{self.pid_file}'. Ollama is not running.")
            # If the PID file exists but the process doesn't, it implies Ollama stopped
            # unexpectedly or the PID file is stale.
            return -3
        except ValueError:
            self.logger.error(f"PID file '{self.pid_file}' contains invalid PID. Please check its content.")
            return -4
        except Exception as e:
            self.logger.error(f"An unexpected error occurred while checking Ollama status: {e}", exc_info=True)
            return -4

    def start_ollama(self) -> int:
        """
        Starts the Ollama server process.

        If Ollama is already running, it will not attempt to start it again.
        The PID of the new process is written to the configured PID file.

        Returns:
            int:
                0: Ollama was successfully started or was already running.
                -1: Failed to start Ollama (e.g., 'ollama' command not found, permissions issue).
                -2: PID file path is not configured, preventing PID tracking.
        """
        if not self.pid_file:
            self.logger.error("PID file path is not configured. Cannot start Ollama and track its PID.")
            return -2

        # Use comprehensive check to see if any ollama processes are running
        status = self.check_ollama_comprehensive()
        serve_processes = [p for p in status['processes'] if p['is_serve']]

        if serve_processes:
            self.logger.info(
                f"Ollama serve is already running (found {len(serve_processes)} serve process(es)). No new process started.")
            # Update PID file with the first serve process if it's not tracked
            if status['pid_file_status'] in ['missing', 'stale', 'invalid']:
                try:
                    with open(self.pid_file, "w") as f:
                        f.write(str(serve_processes[0]['pid']))
                    self.logger.info(f"Updated PID file with existing serve process PID: {serve_processes[0]['pid']}")
                except Exception as e:
                    self.logger.error(f"Failed to update PID file: {e}")
            return 0

        self.logger.info("Attempting to start Ollama server...")
        try:
            # Use `subprocess.Popen` to start `ollama serve` in the background.
            proc = subprocess.Popen(["ollama", "serve"],
                                    stdout=subprocess.DEVNULL,  # Suppress stdout
                                    stderr=subprocess.DEVNULL)  # Suppress stderr

            # Write the PID to the file for later tracking
            with open(self.pid_file, "w") as f:
                f.write(str(proc.pid))
            self.logger.info(
                f"Ollama server started successfully with PID: {proc.pid}. PID written to '{self.pid_file}'.")
            return 0
        except FileNotFoundError:
            self.logger.error("Failed to start Ollama: 'ollama' command not found. "
                              "Please ensure Ollama is installed and in your system's PATH.")
            return -1
        except Exception as e:
            self.logger.error(f"An unexpected error occurred while trying to start Ollama: {e}", exc_info=True)
            return -1

    def force_stop_all_ollama(self) -> int:
        """
        Force stop ALL Ollama processes, not just the one tracked by PID file.
        Use this when you need to ensure Ollama is completely stopped.

        Returns:
            int: 0 if successful, -1 if errors occurred
        """
        errors = 0

        # Find all ollama processes
        ollama_processes = self.find_ollama_processes()

        if not ollama_processes:
            self.logger.info("No Ollama processes found to stop")
            # Clean up PID file if it exists
            if self.pid_file and os.path.exists(self.pid_file):
                try:
                    os.remove(self.pid_file)
                    self.logger.info(f"Removed stale PID file: '{self.pid_file}'")
                except Exception as e:
                    self.logger.error(f"Failed to remove PID file: {e}")
                    errors += 1
            return 0 if errors == 0 else -1

        pids = [p['pid'] for p in ollama_processes]
        self.logger.info(f"Found {len(ollama_processes)} Ollama process(es) to stop: {pids}")

        # Stop each process
        for process_info in ollama_processes:
            pid = process_info['pid']
            try:
                proc = psutil.Process(pid)
                self.logger.info(f"Stopping process {pid} ({proc.name()})...")

                # Graceful termination
                proc.terminate()
                try:
                    proc.wait(timeout=10)
                    self.logger.info(f"Process {pid} terminated gracefully")
                except psutil.TimeoutExpired:
                    self.logger.warning(f"Process {pid} didn't terminate gracefully, killing...")
                    proc.kill()
                    proc.wait()
                    self.logger.info(f"Process {pid} killed forcefully")

            except psutil.NoSuchProcess:
                self.logger.info(f"Process {pid} already gone")
            except psutil.AccessDenied:
                self.logger.error(f"Access denied killing process {pid} - may need elevated privileges")
                errors += 1
            except Exception as e:
                self.logger.error(f"Error stopping process {pid}: {e}")
                errors += 1

        # Clean up PID file
        if self.pid_file and os.path.exists(self.pid_file):
            try:
                os.remove(self.pid_file)
                self.logger.info(f"Removed PID file: '{self.pid_file}'")
            except Exception as e:
                self.logger.error(f"Failed to remove PID file: {e}")
                errors += 1

        return 0 if errors == 0 else -1

    def stop_ollama(self) -> int:
        """
        Stops the running Ollama server process.

        Attempts a graceful termination first (SIGTERM),
        and if the process does not exit within a timeout,
        it resorts to a forceful kill (SIGKILL).
        The PID file is removed upon successful termination.

        Returns:
            int:
                0: Ollama was successfully stopped or was not running.
                -1: PID file path is not configured.
                -2: Error during process termination (e.g., permissions).
                -3: Failed to remove the PID file.
        """
        if not self.pid_file:
            self.logger.error("PID file path is not configured. Cannot stop Ollama definitively.")
            return -1

        # Check current status to avoid errors if already stopped
        status = self.check_ollama()
        if status in {-1, -2, -3, -4}:  # Ollama is not running or PID file issues
            self.logger.info("Ollama server is not running or PID file is invalid. No stop action needed.")
            # Attempt to clean up stale PID file if it exists but process doesn't
            if os.path.exists(self.pid_file):
                try:
                    os.remove(self.pid_file)
                    self.logger.info(f"Removed stale PID file: '{self.pid_file}'.")
                except Exception as e:
                    self.logger.error(f"Failed to remove stale PID file '{self.pid_file}': {e}")
                    return -3  # Indicate PID file cleanup issue
            return 0  # Indicate success in ensuring it's stopped

        try:
            with open(self.pid_file, "r") as f:
                pid = int(f.read().strip())

            proc = psutil.Process(pid)

            # Double-check if it's indeed the Ollama process before terminating
            if "ollama" not in proc.name().lower():
                self.logger.warning(
                    f"PID {pid} from PID file '{self.pid_file}' is not an Ollama process ('{proc.name()}'). "
                    "Skipping termination to prevent unintended process killing.")
                return 0  # Consider it "stopped" from this manager's perspective

            self.logger.info(f"Attempting to gracefully stop Ollama server (PID: {pid})...")
            proc.terminate()  # Send SIGTERM

            try:
                # Wait for the process to terminate, with a timeout
                proc.wait(timeout=10)
                self.logger.info("Ollama server stopped gracefully.")
            except psutil.TimeoutExpired:
                self.logger.warning("Ollama server did not terminate gracefully within 10 seconds. Forcibly killing...")
                proc.kill()  # Send SIGKILL
                proc.wait()  # Wait for the kill to complete
                self.logger.info("Ollama server forcibly killed.")

        except psutil.NoSuchProcess:
            self.logger.info("Ollama process not found (it was likely already stopped).")
            # This can happen if check_ollama returned 0, but the process died
            # between check_ollama and this try block.
        except ValueError:
            self.logger.error(f"PID file '{self.pid_file}' contains invalid PID. Cannot stop process.")
            return -2
        except Exception as e:
            self.logger.error(f"An unexpected error occurred while trying to stop Ollama: {e}", exc_info=True)
            return -2
        finally:
            # Always attempt to remove the PID file if it exists, regardless of termination success
            if os.path.exists(self.pid_file):
                try:
                    os.remove(self.pid_file)
                    self.logger.info(f"Removed PID file: '{self.pid_file}'.")
                except Exception as e:
                    self.logger.error(f"Failed to remove PID file '{self.pid_file}': {e}", exc_info=True)
                    return -3  # Indicate PID file cleanup issue

        return 0

    def interactive_management(self) -> None:
        """
        Interactive management interface for Ollama processes.
        Useful for debugging and manual management.
        """
        while True:
            self.print_diagnosis()

            diagnosis = self.diagnose_ollama_status()

            print("=== Management Options ===")
            print("1. Refresh status")
            print("2. Start Ollama (tracked)")
            print("3. Stop tracked Ollama")
            print("4. Force stop ALL Ollama processes")
            print("5. Exit")

            if diagnosis['total_processes'] > 0:
                print("6. Stop specific process by PID")

            choice = input("\nEnter your choice: ").strip()

            if choice == '1':
                continue
            elif choice == '2':
                result = self.start_ollama()
                print(f"Start result: {result}")
                input("Press Enter to continue...")
            elif choice == '3':
                result = self.stop_ollama()
                print(f"Stop result: {result}")
                input("Press Enter to continue...")
            elif choice == '4':
                confirm = input("Are you sure you want to FORCE STOP ALL Ollama processes? (y/N): ")
                if confirm.lower() == 'y':
                    result = self.force_stop_all_ollama()
                    print(f"Force stop result: {result}")
                input("Press Enter to continue...")
            elif choice == '5':
                break
            elif choice == '6' and diagnosis['total_processes'] > 0:
                pid_input = input("Enter PID to stop: ").strip()
                try:
                    pid = int(pid_input)
                    valid_pids = [p['pid'] for p in diagnosis['processes']]
                    if pid in valid_pids:
                        try:
                            proc = psutil.Process(pid)
                            proc.terminate()
                            proc.wait(timeout=5)
                            print(f"Process {pid} terminated successfully")
                        except psutil.TimeoutExpired:
                            proc.kill()
                            proc.wait()
                            print(f"Process {pid} killed forcefully")
                        except Exception as e:
                            print(f"Error stopping process {pid}: {e}")
                    else:
                        print("PID not found in Ollama processes list.")
                except ValueError:
                    print("Invalid PID entered.")
                input("Press Enter to continue...")
            else:
                print("Invalid choice.")
                input("Press Enter to continue...")