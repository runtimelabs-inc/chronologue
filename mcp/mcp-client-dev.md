# Create project directory
uv init mcp-client
cd mcp-client

# Create virtual environment
uv venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On Unix or MacOS:
source .venv/bin/activate

# Install required packages
uv add mcp anthropic python-dotenv

# Remove boilerplate files
rm main.py

# Create our main file
touch client.py

***

### Setting up your API Key 

# Create .env file
touch .env

Add API key 
https://docs.anthropic.com/en/api/admin-api/apikeys/get-api-key

ANTHROPIC_API_KEY=<your key here>



```
echo ".env" >> .gitignore
```