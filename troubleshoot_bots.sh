#!/bin/bash

# Discord Bot Troubleshooting Script for macOS
# This script helps identify and fix duplicate bot instances

echo "🤖 Discord Bot Troubleshooting Script"
echo "====================================="
echo

# Function to check for running Python processes
check_python_processes() {
    echo "📋 Checking for running Python processes..."
    echo
    
    # Check for any Python processes
    python_procs=$(ps aux | grep -i python | grep -v grep)
    if [ -z "$python_procs" ]; then
        echo "✅ No Python processes found running"
    else
        echo "🔍 Found Python processes:"
        echo "$python_procs"
        echo
    fi
}

# Function to check for Discord bot processes specifically
check_bot_processes() {
    echo "🎯 Checking for Discord bot processes..."
    echo
    
    # Check for MTG card bot
    mtg_procs=$(ps aux | grep -i "mtg" | grep -v grep)
    if [ ! -z "$mtg_procs" ]; then
        echo "🃏 MTG Card Bot processes found:"
        echo "$mtg_procs"
        echo
    fi
    
    # Check for music bot
    music_procs=$(ps aux | grep -i "music" | grep -v grep)
    if [ ! -z "$music_procs" ]; then
        echo "🎵 Music Bot processes found:"
        echo "$music_procs"
        echo
    fi
    
    # Check for clippy bot
    clippy_procs=$(ps aux | grep -i "clippy" | grep -v grep)
    if [ ! -z "$clippy_procs" ]; then
        echo "🔗 Clippy Bot processes found:"
        echo "$clippy_procs"
        echo
    fi
    
    # Check for any discord.py processes
    discord_procs=$(ps aux | grep -i "discord" | grep -v grep)
    if [ ! -z "$discord_procs" ]; then
        echo "💬 Discord-related processes found:"
        echo "$discord_procs"
        echo
    fi
}

# Function to kill all bot processes
kill_bot_processes() {
    echo "⚠️  WARNING: This will kill ALL Discord bot processes!"
    echo "Are you sure you want to continue? (y/N)"
    read -r response
    
    if [[ "$response" =~ ^[Yy]$ ]]; then
        echo
        echo "🛑 Killing Discord bot processes..."
        
        # Step 1: Collect all bot PIDs first
        mtg_pids=$(ps aux | grep -E "(mtg_card_bot|mtg-card-bot)" | grep -v grep | awk '{print $2}')
        music_pids=$(ps aux | grep -E "python.*music" | grep -v grep | awk '{print $2}')
        clippy_pids=$(ps aux | grep -E "python.*clippy" | grep -v grep | awk '{print $2}')
        all_bot_pids="$mtg_pids $music_pids $clippy_pids"
        
        # Remove empty values and duplicates
        unique_pids=$(echo "$all_bot_pids" | tr ' ' '\n' | grep -v '^$' | sort -u | tr '\n' ' ')
        
        if [ -z "$unique_pids" ]; then
            echo "✅ No Discord bot processes found running"
            return
        fi
        
        echo "🎯 Found bot processes with PIDs: $unique_pids"
        echo
        
        # Step 2: Send SIGTERM for graceful shutdown
        echo "📤 Sending graceful shutdown signals..."
        for pid in $unique_pids; do
            if kill -0 "$pid" 2>/dev/null; then
                echo "   Sending SIGTERM to PID $pid"
                kill -TERM "$pid" 2>/dev/null
            fi
        done
        
        # Step 3: Wait for graceful shutdown (up to 8 seconds)
        echo "⏳ Waiting for graceful shutdown (up to 8 seconds)..."
        shutdown_timeout=8
        elapsed=0
        
        while [ $elapsed -lt $shutdown_timeout ]; do
            remaining_pids=""
            for pid in $unique_pids; do
                if kill -0 "$pid" 2>/dev/null; then
                    remaining_pids="$remaining_pids $pid"
                fi
            done
            
            if [ -z "$remaining_pids" ]; then
                echo "✅ All processes shut down gracefully"
                break
            fi
            
            sleep 1
            elapsed=$((elapsed + 1))
            echo "   Waiting... ($elapsed/$shutdown_timeout seconds)"
        done
        
        # Step 4: Force kill any remaining processes
        if [ ! -z "$remaining_pids" ]; then
            echo "💀 Force killing remaining processes..."
            for pid in $remaining_pids; do
                if kill -0 "$pid" 2>/dev/null; then
                    echo "   Force killing PID $pid"
                    kill -KILL "$pid" 2>/dev/null
                    sleep 0.5
                    
                    # Verify the kill worked
                    if kill -0 "$pid" 2>/dev/null; then
                        echo "   ⚠️  Warning: PID $pid still running after SIGKILL"
                    else
                        echo "   ✅ PID $pid terminated"
                    fi
                fi
            done
        fi
        
        # Step 5: Additional cleanup for stubborn processes
        echo "🧹 Performing additional cleanup..."
        
        # Kill by process name patterns (more targeted)
        pkill -f "python.*mtg" 2>/dev/null
        pkill -f "python.*music" 2>/dev/null  
        pkill -f "python.*clippy" 2>/dev/null
        pkill -f "uv run.*mtg" 2>/dev/null
        pkill -f "uv run.*music" 2>/dev/null
        pkill -f "uv run.*clippy" 2>/dev/null
        
        # Wait for cleanup
        sleep 2
        
        echo "✅ Process termination complete"
        echo
        
        # Step 6: Final verification
        echo "🔍 Verifying all processes are terminated..."
        remaining=$(ps aux | grep -E "(mtg_card_bot|mtg-card-bot|python.*music|python.*clippy)" | grep -v grep)
        
        if [ -z "$remaining" ]; then
            echo "✅ All Discord bot processes successfully terminated"
        else
            echo "⚠️  Some processes may still be running:"
            echo "$remaining"
            echo
            
            # Extract PIDs for manual killing
            remaining_pids=$(echo "$remaining" | awk '{print $2}' | tr '\n' ' ')
            echo "🔧 You can manually terminate these with:"
            for pid in $remaining_pids; do
                echo "   kill -9 $pid"
            done
            echo
            echo "Or run this command to kill all at once:"
            echo "   kill -9 $remaining_pids"
        fi
    else
        echo "❌ Operation cancelled"
    fi
}

# Function to check for multiple instances
check_for_duplicates() {
    echo "🔍 Checking for duplicate bot instances..."
    echo
    
    # Count MTG bot instances
    mtg_count=$(ps aux | grep -c "mtg_card_bot\|mtg-card-bot" | grep -v grep)
    if [ "$mtg_count" -gt 1 ]; then
        echo "⚠️  Found $mtg_count MTG Card Bot instances (should be 1 or 0)"
    fi
    
    # Count music bot instances
    music_count=$(ps aux | grep -c "music" | grep -v grep)
    if [ "$music_count" -gt 1 ]; then
        echo "⚠️  Found $music_count Music Bot instances (should be 1 or 0)"
    fi
    
    # Count clippy bot instances
    clippy_count=$(ps aux | grep -c "clippy" | grep -v grep)
    if [ "$clippy_count" -gt 1 ]; then
        echo "⚠️  Found $clippy_count Clippy Bot instances (should be 1 or 0)"
    fi
    
    echo
}

# Function to show port usage
check_ports() {
    echo "🌐 Checking network connections..."
    echo
    
    # Check for any Discord-related network connections
    lsof_output=$(lsof -i | grep -i python 2>/dev/null)
    if [ ! -z "$lsof_output" ]; then
        echo "🔌 Python network connections:"
        echo "$lsof_output"
    else
        echo "✅ No Python network connections found"
    fi
    echo
}

# Function to clean restart
clean_restart() {
    echo "🔄 Performing clean restart of bots..."
    echo
    
    # Kill existing processes (automatically confirms)
    echo "🛑 Terminating existing bot processes..."
    
    # Collect PIDs
    mtg_pids=$(ps aux | grep -E "(mtg_card_bot|mtg-card-bot)" | grep -v grep | awk '{print $2}')
    music_pids=$(ps aux | grep -E "python.*music" | grep -v grep | awk '{print $2}')
    clippy_pids=$(ps aux | grep -E "python.*clippy" | grep -v grep | awk '{print $2}')
    all_bot_pids="$mtg_pids $music_pids $clippy_pids"
    unique_pids=$(echo "$all_bot_pids" | tr ' ' '\n' | grep -v '^$' | sort -u | tr '\n' ' ')
    
    if [ ! -z "$unique_pids" ]; then
        echo "🎯 Terminating processes: $unique_pids"
        
        # Send SIGTERM
        for pid in $unique_pids; do
            if kill -0 "$pid" 2>/dev/null; then
                kill -TERM "$pid" 2>/dev/null
            fi
        done
        
        # Wait for graceful shutdown
        echo "⏳ Waiting for graceful shutdown (5 seconds)..."
        sleep 5
        
        # Force kill any remaining
        for pid in $unique_pids; do
            if kill -0 "$pid" 2>/dev/null; then
                echo "   Force killing PID $pid"
                kill -KILL "$pid" 2>/dev/null
            fi
        done
        
        # Additional cleanup
        pkill -f "python.*mtg" 2>/dev/null
        pkill -f "python.*music" 2>/dev/null  
        pkill -f "python.*clippy" 2>/dev/null
        
        sleep 2
        echo "✅ All processes terminated"
    else
        echo "✅ No existing bot processes found"
    fi
    
    echo
    
    # Check if start_bots.py exists
    if [ -f "start_bots.py" ]; then
        echo "🚀 Starting bots cleanly..."
        python3 start_bots.py
    else
        echo "❌ start_bots.py not found in current directory"
        echo "Please navigate to your bot directory and run this script again"
    fi
}

# Function to kill processes without confirmation (for automation)
kill_bot_processes_auto() {
    echo "🛑 Auto-killing Discord bot processes..."
    
    # Collect PIDs
    mtg_pids=$(ps aux | grep -E "(mtg_card_bot|mtg-card-bot)" | grep -v grep | awk '{print $2}')
    music_pids=$(ps aux | grep -E "python.*music" | grep -v grep | awk '{print $2}')
    clippy_pids=$(ps aux | grep -E "python.*clippy" | grep -v grep | awk '{print $2}')
    all_bot_pids="$mtg_pids $music_pids $clippy_pids"
    unique_pids=$(echo "$all_bot_pids" | tr ' ' '\n' | grep -v '^$' | sort -u | tr '\n' ' ')
    
    if [ -z "$unique_pids" ]; then
        echo "✅ No Discord bot processes found running"
        return
    fi
    
    echo "🎯 Found bot processes with PIDs: $unique_pids"
    
    # Send SIGTERM
    for pid in $unique_pids; do
        if kill -0 "$pid" 2>/dev/null; then
            kill -TERM "$pid" 2>/dev/null
        fi
    done
    
    # Wait for graceful shutdown
    sleep 3
    
    # Force kill any remaining
    for pid in $unique_pids; do
        if kill -0 "$pid" 2>/dev/null; then
            echo "   Force killing PID $pid"
            kill -KILL "$pid" 2>/dev/null
        fi
    done
    
    # Additional cleanup
    pkill -f "python.*mtg" 2>/dev/null
    pkill -f "python.*music" 2>/dev/null  
    pkill -f "python.*clippy" 2>/dev/null
    
    sleep 1
    echo "✅ Process termination complete"
}

# Main menu
show_menu() {
    echo "Choose an option:"
    echo "1) Check for running Python processes"
    echo "2) Check for Discord bot processes"
    echo "3) Check for duplicate instances"
    echo "4) Check network connections"
    echo "5) Kill all bot processes (with confirmation)"
    echo "6) Kill all bot processes (auto, no confirmation)"
    echo "7) Clean restart all bots"
    echo "8) Exit"
    echo
    echo -n "Enter your choice (1-8): "
}

# Main script loop
main() {
    while true; do
        show_menu
        read -r choice
        echo
        
        case $choice in
            1)
                check_python_processes
                ;;
            2)
                check_bot_processes
                ;;
            3)
                check_for_duplicates
                ;;
            4)
                check_ports
                ;;
            5)
                kill_bot_processes
                ;;
            6)
                kill_bot_processes_auto
                ;;
            7)
                clean_restart
                ;;
            8)
                echo "👋 Goodbye!"
                exit 0
                ;;
            *)
                echo "❌ Invalid option. Please choose 1-8."
                ;;
        esac
        
        echo
        echo "Press Enter to continue..."
        read -r
        echo
    done
}

# Run the main function
main
