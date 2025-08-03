#!/usr/bin/env python3
"""
Run MCP Servers Locally
Alternative to Docker for running MCP servers directly on the host machine
"""

import subprocess
import sys
import os
import time
import signal
from pathlib import Path

def install_requirements(server_path):
    """Install requirements for a specific server"""
    requirements_file = server_path / "requirements.txt"
    if requirements_file.exists():
        print(f"📦 Installing requirements for {server_path.name}...")
        try:
            subprocess.run([
                sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
            ], check=True, capture_output=True, text=True)
            print(f"✅ Requirements installed for {server_path.name}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install requirements for {server_path.name}: {e}")
            print(f"   Error output: {e.stderr}")
            return False
    else:
        print(f"⚠️  No requirements.txt found for {server_path.name}")
        return True

def run_server(server_path, env_vars=None):
    """Run a single MCP server"""
    main_file = server_path / "__main__.py"
    if not main_file.exists():
        print(f"❌ Main file not found: {main_file}")
        return None
    
    print(f"🚀 Starting {server_path.name} server...")
    
    # Set up environment
    env = os.environ.copy()
    if env_vars:
        env.update(env_vars)
    
    try:
        process = subprocess.Popen([
            sys.executable, str(main_file)
        ], env=env, cwd=str(server_path))
        
        print(f"✅ {server_path.name} server started with PID {process.pid}")
        return process
    except Exception as e:
        print(f"❌ Failed to start {server_path.name} server: {e}")
        return None

def main():
    """Main function to run MCP servers locally"""
    print("🚀 Running MCP Servers Locally")
    print("=" * 40)
    
    # Get the app directory
    app_dir = Path(__file__).parent
    mcp_servers_dir = app_dir / "mcp-servers"
    
    if not mcp_servers_dir.exists():
        print(f"❌ MCP servers directory not found: {mcp_servers_dir}")
        return
    
    # Server configurations
    servers = {
        "cypher": {
            "path": mcp_servers_dir / "cypher",
            "env": {
                "NEO4J_URI": "bolt://localhost:7687",
                "NEO4J_USER": "neo4j",
                "NEO4J_PASSWORD": "password123"
            }
        },
        "data-modeling": {
            "path": mcp_servers_dir / "data-modeling",
            "env": {
                "POSTGRES_HOST": "localhost",
                "POSTGRES_PORT": "5432",
                "POSTGRES_DB": "movies",
                "POSTGRES_USER": "postgres",
                "POSTGRES_PASSWORD": "password123",
                "NEO4J_URI": "bolt://localhost:7687",
                "NEO4J_USER": "neo4j",
                "NEO4J_PASSWORD": "password123"
            }
        }
    }
    
    # Install requirements for all servers
    print("📦 Installing Requirements...")
    for server_name, config in servers.items():
        if not install_requirements(config["path"]):
            print(f"❌ Failed to install requirements for {server_name}")
            return
    
    print("\n🚀 Starting Servers...")
    processes = []
    
    # Start all servers
    for server_name, config in servers.items():
        process = run_server(config["path"], config["env"])
        if process:
            processes.append((server_name, process))
        else:
            print(f"❌ Failed to start {server_name} server")
    
    if not processes:
        print("❌ No servers started successfully")
        return
    
    print(f"\n✅ Started {len(processes)} MCP servers")
    print("\n📋 Running Servers:")
    for server_name, process in processes:
        print(f"  🔧 {server_name}: PID {process.pid}")
    
    print("\n💡 Usage:")
    print("- Add these servers to your Claude Desktop configuration")
    print("- Use Ctrl+C to stop all servers")
    print("- Check logs if servers fail to start")
    
    # Wait for interrupt
    try:
        print("\n⏳ Servers running... Press Ctrl+C to stop")
        while True:
            # Check if any process has died
            for server_name, process in processes[:]:
                if process.poll() is not None:
                    print(f"⚠️  {server_name} server stopped (exit code: {process.returncode})")
                    processes.remove((server_name, process))
            
            if not processes:
                print("❌ All servers have stopped")
                break
            
            time.sleep(1)
    
    except KeyboardInterrupt:
        print("\n🛑 Stopping servers...")
        
        # Terminate all processes
        for server_name, process in processes:
            print(f"🛑 Stopping {server_name} server...")
            process.terminate()
            
            # Wait for graceful shutdown
            try:
                process.wait(timeout=5)
                print(f"✅ {server_name} server stopped")
            except subprocess.TimeoutExpired:
                print(f"⚠️  Force killing {server_name} server...")
                process.kill()
                process.wait()
        
        print("✅ All servers stopped")

def test_server_files():
    """Test if server files are accessible"""
    print("🔍 Testing Server Files")
    print("-" * 30)
    
    app_dir = Path(__file__).parent
    mcp_servers_dir = app_dir / "mcp-servers"
    
    servers = ["cypher", "data-modeling"]
    
    for server_name in servers:
        server_path = mcp_servers_dir / server_name
        main_file = server_path / "__main__.py"
        requirements_file = server_path / "requirements.txt"
        
        print(f"\n📁 {server_name}:")
        print(f"  Path: {server_path}")
        print(f"  Exists: {server_path.exists()}")
        print(f"  Main file: {main_file.exists()}")
        print(f"  Requirements: {requirements_file.exists()}")
        
        if main_file.exists():
            # Try to read the first few lines
            try:
                with open(main_file, 'r') as f:
                    first_line = f.readline().strip()
                    print(f"  First line: {first_line}")
            except Exception as e:
                print(f"  Error reading: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_server_files()
    else:
        main()