"""
Debug script for testing MCP handler without Azure OpenAI
"""
import sys
import os

# Add the src/python directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_mcp_handler_offline():
    """Test the MCP handler with mock responses (no Azure OpenAI needed)"""
    print("🧪 Testing MCP Handler (Offline Mode)")
    print("=" * 50)
    
    # Mock the interpret_command function for testing
    def mock_interpret_command(nl_command):
        """Mock interpretation without calling Azure OpenAI"""
        test_mappings = {
            "pick up block from position 3": "get_block 3",
            "place block at position 7": "put_block 7", 
            "what color is the block": "get_color",
            "are you holding anything": "holding_block",
            "check if block exists at position 5": "block_exists 5",
            "scan the row": "scan_row"
        }
        
        nl_lower = nl_command.lower()
        for key, value in test_mappings.items():
            if key in nl_lower:
                return value
        
        # Try to extract numbers for position-based commands
        if "pick up" in nl_lower or "get block" in nl_lower:
            import re
            match = re.search(r'\d+', nl_command)
            if match:
                return f"get_block {match.group()}"
        
        if "place" in nl_lower or "put block" in nl_lower:
            import re
            match = re.search(r'\d+', nl_command)
            if match:
                return f"put_block {match.group()}"
        
        return "command unknown"
    
    # Import and temporarily replace the function
    try:
        from mcp_handler import validate_command, send_to_xarm
        import mcp_handler
        
        # Temporarily replace the interpret_command function
        original_interpret = mcp_handler.interpret_command
        mcp_handler.interpret_command = mock_interpret_command
        
        # Test cases
        test_commands = [
            "Pick up the block from position 3",
            "Place the block at position 7",
            "What color is the block?", 
            "Are you holding anything?",
            "Check if there's a block at position 5",
            "Scan the row for blocks",
            "Invalid command test"
        ]
        
        print("Running test cases:")
        print("-" * 30)
        
        for i, cmd in enumerate(test_commands, 1):
            print(f"\n{i}. Testing: '{cmd}'")
            
            # Test interpretation
            interpreted = mock_interpret_command(cmd)
            print(f"   Interpreted: {interpreted}")
            
            # Test validation
            is_valid = validate_command(interpreted)
            print(f"   Valid: {is_valid}")
            
            # Test xARM response
            if is_valid:
                response = send_to_xarm(interpreted)
                print(f"   xARM Response: {response}")
            
        # Restore original function
        mcp_handler.interpret_command = original_interpret
        
        print(f"\n✅ Offline testing completed!")
        
    except ImportError as e:
        print(f"❌ Could not import mcp_handler: {e}")
        print("Make sure you're in the right directory and dependencies are installed.")

# TODO: Replace the mock implementation with actual serial communication
# This should use the serial connection from main.py like this:

async def send_to_xarm_real(command, serial_connection, serial_lock):
    async with serial_lock:
        serial_msg = f"{command}\n"
        serial_connection.write(serial_msg.encode())
        # Wait for response from Arduino
        response = await wait_for_arduino_response(serial_connection)
        return response

if __name__ == "__main__":
    test_mcp_handler_offline()
