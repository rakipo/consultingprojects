#!/usr/bin/env python3
"""
Claude Desktop MCP Configuration Setup
Helps configure MCP servers for Claude Desktop
"""

import json
import os
import platform
from pathlib import Path

def get_claude_config_path():
    """Get the Claude Desktop configuration path based on OS"""
    system = platform.system()
    
    if system == "Darwin":  # macOS
        return Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    elif system == "Windows":
        return Path.home() / "AppData" / "Roaming" / "Claude" / "claude_desktop_config.json"
    elif system == "Linux":
        return Path.home() / ".config" / "Claude" / "claude_desktop_config.json"
    else:
        raise ValueError(f"Unsupported operating system: {system}")

def get_current_directory():
    """Get the current project directory"""
    return Path(__file__).parent.absolute()

def create_mcp_config():
    """Create MCP configuration for Claude Desktop"""
    current_dir = get_current_directory()
    
    # MCP Server configurations
    config = {
        "mcpServers": {
            "neo4j-cypher": {
                "command": "python",
                "args": [str(current_dir / "mcp-servers" / "cypher" / "__main__.py")],
                "env": {
                    "NEO4J_URI": "bolt://localhost:7687",
                    "NEO4J_USER": "neo4j",
                    "NEO4J_PASSWORD": "password123"
                }
            },
            "neo4j-data-modeling": {
                "command": "python",
                "args": [str(current_dir / "mcp-servers" / "data-modeling" / "__main__.py")],
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
    }
    
    return config

def setup_claude_desktop():
    """Setup Claude Desktop MCP configuration"""
    print("🚀 Claude Desktop MCP Configuration Setup")
    print("=" * 50)
    
    try:
        # Get Claude config path
        claude_config_path = get_claude_config_path()
        print(f"📁 Claude config path: {claude_config_path}")
        
        # Create directory if it doesn't exist
        claude_config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create MCP configuration
        mcp_config = create_mcp_config()
        
        # Check if config file already exists
        existing_config = {}
        if claude_config_path.exists():
            print("📋 Existing Claude config found, merging...")
            with open(claude_config_path, 'r') as f:
                existing_config = json.load(f)
        
        # Merge configurations
        if "mcpServers" not in existing_config:
            existing_config["mcpServers"] = {}
        
        existing_config["mcpServers"].update(mcp_config["mcpServers"])
        
        # Write configuration
        with open(claude_config_path, 'w') as f:
            json.dump(existing_config, f, indent=2)
        
        print("✅ Claude Desktop configuration updated successfully!")
        
        # Save a backup copy in the project
        backup_path = Path(__file__).parent / "claude-desktop-mcp-config.json"
        with open(backup_path, 'w') as f:
            json.dump(mcp_config, f, indent=2)
        print(f"💾 Backup configuration saved to: {backup_path}")
        
        # Show configuration
        print("\n📋 MCP Servers configured:")
        for server_name, server_config in mcp_config["mcpServers"].items():
            print(f"  🔧 {server_name}")
            print(f"     Command: {server_config['command']} {' '.join(server_config['args'])}")
            print(f"     Environment: {len(server_config['env'])} variables")
        
        print("\n🔄 Next Steps:")
        print("1. Restart Claude Desktop application")
        print("2. The MCP servers should appear in Claude's interface")
        print("3. Make sure Docker containers are running:")
        print("   docker-compose -f docker-compose-mcp.yml ps")
        
        return True
        
    except Exception as e:
        print(f"❌ Error setting up Claude Desktop configuration: {e}")
        return False

def verify_setup():
    """Verify the setup is correct"""
    print("\n🔍 Verifying Setup")
    print("-" * 30)
    
    current_dir = get_current_directory()
    
    # Check if MCP server files exist
    cypher_main = current_dir / "mcp-servers" / "cypher" / "__main__.py"
    data_modeling_main = current_dir / "mcp-servers" / "data-modeling" / "__main__.py"
    
    if cypher_main.exists():
        print("✅ Neo4j Cypher server file exists")
    else:
        print(f"❌ Neo4j Cypher server file missing: {cypher_main}")
    
    if data_modeling_main.exists():
        print("✅ Data modeling server file exists")
    else:
        print(f"❌ Data modeling server file missing: {data_modeling_main}")
    
    # Check if requirements.txt exists
    requirements_file = current_dir / "requirements.txt"
    if requirements_file.exists():
        print("✅ Requirements file exists")
    else:
        print(f"❌ Requirements file missing: {requirements_file}")
    
    # Check Claude config
    try:
        claude_config_path = get_claude_config_path()
        if claude_config_path.exists():
            print("✅ Claude Desktop config file exists")
            with open(claude_config_path, 'r') as f:
                config = json.load(f)
                if "mcpServers" in config:
                    servers = list(config["mcpServers"].keys())
                    print(f"📋 Configured MCP servers: {', '.join(servers)}")
                else:
                    print("⚠️  No MCP servers configured")
        else:
            print("❌ Claude Desktop config file not found")
    except Exception as e:
        print(f"⚠️  Could not check Claude config: {e}")

def show_manual_instructions():
    """Show manual configuration instructions"""
    print("\n📖 Manual Configuration Instructions")
    print("=" * 40)
    
    current_dir = get_current_directory()
    
    print("If automatic setup doesn't work, manually add this to your Claude Desktop config:")
    print(f"Location: {get_claude_config_path()}")
    print("\nConfiguration to add:")
    
    config = create_mcp_config()
    print(json.dumps(config, indent=2))
    
    print("\n🔧 Environment Setup:")
    print("Make sure these are running:")
    print("1. Docker containers: docker-compose -f docker-compose-mcp.yml up -d")
    print("2. Neo4j accessible at bolt://localhost:7687")
    print("3. PostgreSQL accessible at localhost:5432")

def main():
    """Main setup function"""
    try:
        success = setup_claude_desktop()
        verify_setup()
        
        if not success:
            show_manual_instructions()
        
        print("\n🎉 Setup complete!")
        print("Restart Claude Desktop to use the MCP servers.")
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        show_manual_instructions()

if __name__ == "__main__":
    main()