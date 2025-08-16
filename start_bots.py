#!/usr/bin/env python3
"""
Discord Bots Startup Script
Interactive CLI for managing Python Discord bots - Standard library only
"""

import os
import signal
import subprocess
import sys
import threading
import time
import select
from pathlib import Path
from typing import Dict, List, Optional

if os.name == 'posix':
    import termios
    import tty


class BotManager:
    def __init__(self):
        self.bots: Dict[str, Dict] = {}
        self.processes: Dict[str, subprocess.Popen] = {}
        self.selected_index = 0
        self.menu_items: List[str] = []
        
    def scan_bots(self) -> None:
        """Scan the bots directory for available bots."""
        bots_dir = Path("bots")
        if not bots_dir.exists():
            print("❌ No 'bots' directory found!")
            return
            
        for bot_dir in bots_dir.iterdir():
            if bot_dir.is_dir() and (bot_dir / "pyproject.toml").exists():
                # Read pyproject.toml to get bot info
                try:
                    with open(bot_dir / "pyproject.toml", "r") as f:
                        content = f.read()
                        
                    # Extract name and description
                    name = None
                    description = None
                    package_name = None
                    
                    for line in content.split("\n"):
                        if line.startswith("name = "):
                            package_name = line.split("=", 1)[1].strip().strip('"')
                        elif line.startswith("description = "):
                            description = line.split("=", 1)[1].strip().strip('"')
                    
                    if package_name:
                        # Create display name from directory name
                        display_name = bot_dir.name.replace("-", " ").title()
                        
                        self.bots[bot_dir.name] = {
                            "name": display_name,
                            "description": description or "Discord bot",
                            "package_name": package_name,
                            "path": bot_dir,
                            "module": self._get_module_name(bot_dir),
                        }
                        
                except Exception as e:
                    print(f"⚠️  Error reading {bot_dir}/pyproject.toml: {e}")
    
    def _get_module_name(self, bot_dir: Path) -> str:
        """Get the Python module name for the bot."""
        src_dir = bot_dir / "src"
        if src_dir.exists():
            for item in src_dir.iterdir():
                if item.is_dir() and (item / "__main__.py").exists():
                    return item.name
        return bot_dir.name.replace("-", "_")
    
    def load_env_file(self) -> None:
        """Load environment variables from .env file."""
        env_file = Path(".env")
        if env_file.exists():
            print("📋 Loading environment variables from .env file...")
            with open(env_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        os.environ[key.strip()] = value.strip()
        else:
            print("⚠️  No .env file found. Using environment variables only.")
    
    def check_required_tokens(self, bot_keys: List[str]) -> List[str]:
        """Check for required Discord tokens."""
        # Map bot directory names to their actual environment variable names
        token_map = {
            "clippy": "CLIPPY_DISCORD_TOKEN",
            "mtg-card-bot": "MTG_DISCORD_TOKEN", 
            "music": "MUSIC_DISCORD_TOKEN"
        }
        
        missing = []
        for bot_key in bot_keys:
            env_var = token_map.get(bot_key, f"{bot_key.upper().replace('-', '_')}_DISCORD_TOKEN")
            if not os.environ.get(env_var):
                missing.append(env_var)
        return missing
    
    def clear_screen(self) -> None:
        """Clear the terminal screen."""
        os.system('clear' if os.name == 'posix' else 'cls')
    
    def display_menu(self) -> None:
        """Display the interactive menu."""
        self.clear_screen()
        
        print("🤖 Python Discord Bots Manager")
        print("=" * 40)
        print()
        
        # Build menu items
        self.menu_items = ["🚀 Start All Bots"]
        for bot_key, bot_info in self.bots.items():
            emoji = self._get_bot_emoji(bot_key)
            self.menu_items.append(f"{emoji} Start {bot_info['name']}")
        self.menu_items.append("❌ Exit")
        
        # Display menu items
        for i, item in enumerate(self.menu_items):
            if i == self.selected_index:
                print(f"→ {item}")
            else:
                print(f"  {item}")
        
        print()
        print("Use ↑/↓ arrow keys to navigate, Enter to select, q to quit")
        if self.bots:
            print(f"\nFound {len(self.bots)} bot(s):")
            for bot_key, bot_info in self.bots.items():
                print(f"  • {bot_info['name']}: {bot_info['description']}")
    
    def _get_bot_emoji(self, bot_key: str) -> str:
        """Get emoji for bot based on its name."""
        if "clippy" in bot_key.lower():
            return "🔗"
        elif "mtg" in bot_key.lower():
            return "🃏"
        elif "music" in bot_key.lower():
            return "🎵"
        else:
            return "🤖"
    
    def get_key(self) -> str:
        """Get a single keypress from the user."""
        if os.name == 'posix':
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setcbreak(fd)
                key = sys.stdin.read(1)
                
                # Handle arrow keys (escape sequences)
                if key == '\x1b':  # ESC sequence
                    next1 = sys.stdin.read(1)
                    next2 = sys.stdin.read(1)
                    if next1 == '[':
                        if next2 == 'A':
                            return 'up'
                        elif next2 == 'B':
                            return 'down'
                return key
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        else:
            # Windows fallback - simple input
            return input("Enter choice (1-{}, q to quit): ".format(len(self.menu_items)))
    
    def handle_input(self) -> None:
        """Handle keyboard input for menu navigation."""
        while True:
            try:
                key = self.get_key()
                
                if key == 'up':
                    self.selected_index = (self.selected_index - 1) % len(self.menu_items)
                    self.display_menu()
                elif key == 'down':
                    self.selected_index = (self.selected_index + 1) % len(self.menu_items)
                    self.display_menu()
                elif key == '\r' or key == '\n':  # Enter
                    self.execute_selection()
                    break
                elif key == 'q' or key == 'Q':
                    print("\n👋 Goodbye!")
                    sys.exit(0)
                elif key.isdigit():
                    # Allow numeric selection
                    choice = int(key) - 1
                    if 0 <= choice < len(self.menu_items):
                        self.selected_index = choice
                        self.execute_selection()
                        break
                        
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                sys.exit(0)
            except Exception:
                # Fallback for any terminal issues
                break
    
    def simple_menu(self) -> None:
        """Fallback simple menu for systems without proper terminal support."""
        while True:
            self.display_menu()
            print("\nSelect an option:")
            for i, item in enumerate(self.menu_items, 1):
                print(f"{i}. {item}")
            
            try:
                choice = input("\nEnter your choice (number or 'q' to quit): ").strip()
                
                if choice.lower() == 'q':
                    print("👋 Goodbye!")
                    sys.exit(0)
                
                if choice.isdigit():
                    index = int(choice) - 1
                    if 0 <= index < len(self.menu_items):
                        self.selected_index = index
                        self.execute_selection()
                        break
                    else:
                        print("Invalid choice. Please try again.")
                        time.sleep(1)
                else:
                    print("Invalid choice. Please try again.")
                    time.sleep(1)
                    
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                sys.exit(0)
    
    def execute_selection(self) -> None:
        """Execute the selected menu option."""
        selection = self.menu_items[self.selected_index]
        
        if "Start All Bots" in selection:
            self.start_all_bots()
        elif "Exit" in selection:
            print("\n👋 Goodbye!")
            sys.exit(0)
        else:
            # Extract bot name and start single bot
            for bot_key, bot_info in self.bots.items():
                if bot_info['name'] in selection:
                    self.start_single_bot(bot_key)
                    break
    
    def start_all_bots(self) -> None:
        """Start all bots concurrently."""
        if not self.bots:
            print("❌ No bots found!")
            input("Press Enter to continue...")
            return
        
        # Check tokens for all bots
        missing_tokens = self.check_required_tokens(list(self.bots.keys()))
        if missing_tokens:
            print("❌ Missing required environment variables:")
            for token in missing_tokens:
                print(f"   - {token}")
            print("\nPlease set these variables or create a .env file")
            input("Press Enter to continue...")
            return
        
        self.clear_screen()
        print("🚀 Starting all bots...")
        print("Press Ctrl+C to stop all bots")
        print()
        
        # Start all bots
        for bot_key, bot_info in self.bots.items():
            self._start_bot_process(bot_key, bot_info)
        
        # Set up signal handlers for cleanup
        signal.signal(signal.SIGINT, self._cleanup_handler)
        signal.signal(signal.SIGTERM, self._cleanup_handler)
        
        print("✅ All bots started successfully!")
        process_info = []
        for bot_key, proc in self.processes.items():
            bot_name = self.bots[bot_key]["name"]
            process_info.append(f"{bot_name} (PID: {proc.pid})")
        print(f"   Processes: {', '.join(process_info)}")
        print("\nLogs are displayed below. Press Ctrl+C to stop all bots.")
        
        # Wait for all processes
        try:
            for process in self.processes.values():
                process.wait()
        except KeyboardInterrupt:
            self._cleanup_all()
    
    def start_single_bot(self, bot_key: str) -> None:
        """Start a single bot."""
        bot_info = self.bots[bot_key]
        
        # Check token for this bot
        missing_tokens = self.check_required_tokens([bot_key])
        if missing_tokens:
            print(f"❌ Missing environment variable: {missing_tokens[0]}")
            input("Press Enter to continue...")
            return
        
        self.clear_screen()
        print(f"🚀 Starting {bot_info['name']}...")
        print("Press Ctrl+C to stop the bot")
        print()
        
        # Start the bot
        self._start_bot_process(bot_key, bot_info)
        
        # Set up signal handlers for cleanup
        signal.signal(signal.SIGINT, self._cleanup_handler)
        signal.signal(signal.SIGTERM, self._cleanup_handler)
        
        print(f"✅ {bot_info['name']} started successfully! (PID: {self.processes[bot_key].pid})")
        print("\nPress Ctrl+C to stop the bot.")
        
        # Wait for the process
        try:
            self.processes[bot_key].wait()
        except KeyboardInterrupt:
            self._cleanup_all()
    
    def _start_bot_process(self, bot_key: str, bot_info: Dict) -> None:
        """Start a bot process."""
        try:
            cmd = ["uv", "run", "--package", bot_info["package_name"], "python", "-m", bot_info["module"]]
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            self.processes[bot_key] = process
            
            # Start thread to handle output
            threading.Thread(
                target=self._handle_bot_output,
                args=(bot_key, process),
                daemon=True
            ).start()
            
        except Exception as e:
            print(f"❌ Failed to start {bot_info['name']}: {e}")
    
    def _handle_bot_output(self, bot_key: str, process: subprocess.Popen) -> None:
        """Handle output from a bot process."""
        bot_name = self.bots[bot_key]["name"].upper()
        
        while True:
            line = process.stdout.readline()
            if not line:
                break
            print(f"[{bot_name}] {line.rstrip()}")
    
    def _cleanup_handler(self, signum, frame):
        """Handle cleanup on signal."""
        print(f"\n🛑 Received signal {signum}, stopping all bots...")
        self._cleanup_all()
    
    def _cleanup_all(self) -> None:
        """Clean up all running processes with enhanced shutdown."""
        if not hasattr(self, '_cleanup_called'):
            self._cleanup_called = True
        else:
            print("Cleanup already in progress...")
            return
            
        if not self.processes:
            print("✅ No processes to cleanup")
            sys.exit(0)
            
        print("🛑 Initiating graceful shutdown of all bots...")
        
        # Step 1: Send SIGTERM to all processes for graceful shutdown
        for bot_key, process in self.processes.items():
            if process.poll() is None:  # Process is still running
                bot_name = self.bots[bot_key]["name"]
                print(f"   Sending shutdown signal to {bot_name} (PID: {process.pid})...")
                try:
                    process.terminate()
                except Exception as e:
                    print(f"   Error sending shutdown signal to {bot_name}: {e}")
        
        # Step 2: Wait for graceful shutdown (up to 8 seconds total)
        shutdown_timeout = 8
        start_time = time.time()
        remaining_processes = list(self.processes.items())
        
        while remaining_processes and (time.time() - start_time) < shutdown_timeout:
            still_running = []
            for bot_key, process in remaining_processes:
                if process.poll() is None:
                    still_running.append((bot_key, process))
                else:
                    bot_name = self.bots[bot_key]["name"]
                    print(f"   ✅ {bot_name} shut down gracefully")
            
            remaining_processes = still_running
            if remaining_processes:
                time.sleep(0.5)
        
        # Step 3: Force kill any remaining processes
        if remaining_processes:
            print("   Some processes require force termination...")
            for bot_key, process in remaining_processes:
                if process.poll() is None:
                    bot_name = self.bots[bot_key]["name"]
                    print(f"   Force killing {bot_name} (PID: {process.pid})...")
                    try:
                        process.kill()
                        process.wait(timeout=3)
                        print(f"   ✅ {bot_name} force terminated")
                    except subprocess.TimeoutExpired:
                        print(f"   ⚠️  Warning: Could not kill {bot_name} (PID: {process.pid})")
                        print(f"      You may need to manually kill with: kill -9 {process.pid}")
                    except Exception as e:
                        print(f"   Error force killing {bot_name}: {e}")
        
        # Step 4: Final cleanup and verification
        time.sleep(0.5)  # Brief pause for processes to fully terminate
        
        # Check for any remaining processes
        remaining_pids = []
        for bot_key, process in self.processes.items():
            if process.poll() is None:
                remaining_pids.append(process.pid)
        
        if remaining_pids:
            print(f"⚠️  Warning: Some processes may still be running: {remaining_pids}")
            print("   You can manually terminate them with:")
            for pid in remaining_pids:
                print(f"   kill -9 {pid}")
        else:
            print("✅ All bots stopped successfully")
        
        sys.exit(0)
    
    def run(self) -> None:
        """Run the bot manager."""
        print("🤖 Initializing Python Discord Bots Manager...")
        
        # Load environment variables
        self.load_env_file()
        
        # Scan for bots
        self.scan_bots()
        
        if not self.bots:
            print("❌ No bots found in the 'bots' directory!")
            print("Make sure you have bot directories with pyproject.toml files.")
            sys.exit(1)
        
        # Sync dependencies
        print("📦 Syncing dependencies...")
        try:
            subprocess.run(["uv", "sync", "--all-extras"], check=True, capture_output=True)
            print("✅ Dependencies synced")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to sync dependencies: {e}")
            sys.exit(1)
        
        print()
        
        # Display menu and handle input
        self.display_menu()
        
        # Try advanced terminal input, fallback to simple menu
        try:
            if os.name == 'posix':
                self.handle_input()
            else:
                self.simple_menu()
        except Exception:
            # Fallback to simple menu if terminal handling fails
            print("Using simple menu mode...")
            self.simple_menu()


def main():
    """Main entry point."""
    try:
        manager = BotManager()
        manager.run()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()