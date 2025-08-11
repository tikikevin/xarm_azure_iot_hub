"""
MCP Handler with optional Azure OpenAI integration for debugging
"""
import os
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging for debugging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load Azure OpenAI configuration from environment variables
AZURE_OPENAI_API_KEY = os.getenv('AZURE_OPENAI_API_KEY')
AZURE_OPENAI_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT')
AZURE_OPENAI_DEPLOYMENT = os.getenv('AZURE_OPENAI_DEPLOYMENT')

# Check if Azure OpenAI is configured
AZURE_OPENAI_AVAILABLE = all([AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_DEPLOYMENT])

if AZURE_OPENAI_AVAILABLE:
    logger.info("✅ Azure OpenAI configuration found")
    try:
        from openai import AzureOpenAI
    except ImportError:
        logger.warning("OpenAI package not found. Install with: pip install openai")
        AZURE_OPENAI_AVAILABLE = False
else:
    logger.warning("⚠️ Azure OpenAI not configured - using mock responses")
    logger.info("Set these environment variables to enable Azure OpenAI:")
    logger.info("- AZURE_OPENAI_API_KEY")
    logger.info("- AZURE_OPENAI_ENDPOINT") 
    logger.info("- AZURE_OPENAI_DEPLOYMENT")

def mock_interpret_command(natural_language_command):
    """
    Mock interpretation without calling Azure OpenAI for debugging
    """
    logger.debug(f"Using mock interpretation for: {natural_language_command}")
    
    nl_lower = natural_language_command.lower()
    
    # Simple pattern matching for common commands
    if "pick up" in nl_lower or "get block" in nl_lower:
        import re
        match = re.search(r'position\s*(\d+)|from\s*(\d+)', nl_lower)
        if match:
            pos = match.group(1) or match.group(2)
            return f"get_block {pos}"
        return "get_block 1"  # Default
    
    elif "place" in nl_lower or "put block" in nl_lower:
        import re
        match = re.search(r'position\s*(\d+)|at\s*(\d+)', nl_lower)
        if match:
            pos = match.group(1) or match.group(2)
            return f"put_block {pos}"
        return "put_block 1"  # Default
    
    elif "color" in nl_lower:
        return "get_color"
    
    elif "holding" in nl_lower:
        return "holding_block"
    
    elif "exists" in nl_lower or "check" in nl_lower:
        import re
        match = re.search(r'position\s*(\d+)|at\s*(\d+)', nl_lower)
        if match:
            pos = match.group(1) or match.group(2)
            return f"block_exists {pos}"
        return "block_exists 1"  # Default
    
    elif "scan" in nl_lower:
        return "scan_row"
    
    else:
        return "command unknown"

def interpret_command(natural_language_command):
    """
    Send a natural language command to Azure OpenAI and get the interpreted robotic method.
    Falls back to mock responses if Azure OpenAI is not available.
    """
    logger.debug(f"Interpreting command: {natural_language_command}")
    
    if not AZURE_OPENAI_AVAILABLE:
        return mock_interpret_command(natural_language_command)
    
    try:
        client = AzureOpenAI(
            api_key=AZURE_OPENAI_API_KEY,
            api_version="2024-02-01",
            azure_endpoint=AZURE_OPENAI_ENDPOINT
        )

        system_prompt = """You are an AI handler for xARM robotic arm. 
        Translate user natural language commands to specific xARM method calls.
        
        Available xARM commands:
        - get_block X (where X is position 1-9): Pick up block from position X
        - put_block X (where X is position 1-9): Place block at position X  
        - get_color: Get the color of current block
        - holding_block: Check if arm is holding a block
        - block_exists X: Check if block exists at position X
        - scan_row: Scan the row for blocks
        
        Examples:
        "Pick up the block from position 3" → "get_block 3"
        "Place the block at position 7" → "put_block 7"
        "What color is the block?" → "get_color"
        "Are you holding anything?" → "holding_block"
        
        Return ONLY the command, no explanations."""

        response = client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": natural_language_command}
            ],
            max_tokens=100,
            temperature=0.1  # Low temperature for consistent responses
        )
        
        interpreted_command = response.choices[0].message.content.strip()
        logger.debug(f"Azure OpenAI response: {interpreted_command}")
        return interpreted_command
        
    except Exception as e:
        logger.error(f"Error calling Azure OpenAI: {e}")
        logger.info("Falling back to mock interpretation")
        return mock_interpret_command(natural_language_command)

def send_to_xarm(command):
    """
    Send the interpreted command to the xARM device (stub for now).
    In production, this should use the serial connection from main.py
    """
    logger.debug(f"Sending command to xARM: {command}")
    
    # TODO: Implement actual serial communication
    # This should integrate with the serial connection from main.py
    # For now, just simulate the response
    print(f"🤖 Sending to xARM: {command}")
    
    # Simulate response based on command type
    if command.startswith("get_block"):
        return f"{command}: true"
    elif command.startswith("put_block"):
        return f"{command}: true"
    elif command == "get_color":
        return "get_color: red"  # Simulate a color response
    elif command == "holding_block":
        return "holding_block: false"
    elif command.startsWith("block_exists"):
        return f"{command}: true"
    elif command == "scan_row":
        return "scan_row: 3"  # Simulate finding block at position 3
    else:
        return "command unknown"

def validate_command(command):
    """
    Validate that the interpreted command is a valid xARM command.
    """
    valid_commands = [
        "get_block", "put_block", "get_color", 
        "holding_block", "block_exists", "scan_row"
    ]
    
    command_parts = command.strip().split()
    if not command_parts:
        return False
    
    base_command = command_parts[0]
    if base_command not in valid_commands:
        logger.warning(f"Invalid command: {base_command}")
        return False
    
    # Validate position parameters for commands that need them
    if base_command in ["get_block", "put_block", "block_exists"]:
        if len(command_parts) != 2:
            logger.warning(f"Command {base_command} requires a position parameter")
            return False
        try:
            position = int(command_parts[1])
            if not 1 <= position <= 9:
                logger.warning(f"Position {position} out of range (1-9)")
                return False
        except ValueError:
            logger.warning(f"Invalid position parameter: {command_parts[1]}")
            return False
    
    return True

def handle_natural_language_command(nl_command):
    """
    Main handler function with enhanced debugging and validation.
    """
    logger.info(f"Processing natural language command: {nl_command}")
    
    try:
        # Step 1: Interpret the command
        interpreted = interpret_command(nl_command)
        logger.debug(f"Interpreted command: {interpreted}")
        
        # Step 2: Validate the interpreted command
        if not validate_command(interpreted):
            error_msg = f"Invalid interpreted command: {interpreted}"
            logger.error(error_msg)
            return error_msg
        
        # Step 3: Send to xARM
        response = send_to_xarm(interpreted)
        logger.info(f"xARM response: {response}")
        
        return {
            "natural_language": nl_command,
            "interpreted": interpreted,
            "xarm_response": response
        }
        
    except Exception as e:
        error_msg = f"Error processing command: {str(e)}"
        logger.error(error_msg)
        return error_msg

if __name__ == "__main__":
    print("🤖 xARM MCP Handler - Debug Mode")
    print("=" * 50)
    
    if AZURE_OPENAI_AVAILABLE:
        print("✅ Azure OpenAI is configured and will be used")
    else:
        print("⚠️ Azure OpenAI not configured - using mock responses")
        print("This is perfect for testing the logic without API calls!")
    
    print("\nTest commands you can try:")
    print("- 'Pick up the block from position 3'")
    print("- 'Place the block at position 7'") 
    print("- 'What color is the block?'")
    print("- 'Are you holding anything?'")
    print("- 'Check if there's a block at position 5'")
    print("- 'Scan the row for blocks'")
    print("\nType 'exit' to quit\n")
    
    while True:
        try:
            cmd = input("Enter a natural language command for xARM: ").strip()
            if cmd.lower() in ['exit', 'quit']:
                break
            if not cmd:
                continue
                
            result = handle_natural_language_command(cmd)
            print(f"\n📋 Result: {result}")
            print("-" * 30)
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            print(f"❌ Error: {e}")
