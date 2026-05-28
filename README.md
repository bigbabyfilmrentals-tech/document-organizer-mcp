# Workspace MCP Server

A minimal Python MCP server built with the official MCP Python SDK and prepared for deployment on Render from GitHub.

## Files

- `server.py`: the MCP server entrypoint
- `requirements.txt`: Python dependencies
- `render.yaml`: Render deployment blueprint

## What this server does

This starter server exposes:

- `echo`: returns the text you send it
- `add_numbers`: adds two numbers
- `list_workspace_files`: lists files inside the app directory
- `read_text_file`: reads a UTF-8 text file
- `read_json_file`: reads and parses a JSON file

It also exposes a resource at `workspace://server-info`.

## Run locally

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Run in local stdio mode:

   ```bash
   python server.py
   ```

3. Run in MCP dev mode:

   ```bash
   uv run mcp dev server.py
   ```

4. Run in HTTP mode locally:

   ```bash
   MCP_TRANSPORT=streamable-http python server.py
   ```

By default, local HTTP mode listens on `127.0.0.1:8000`, and the MCP endpoint is:

```text
http://127.0.0.1:8000/mcp
```

## Deploy on Render

### Option 1: Use `render.yaml`

1. Push these files to your GitHub repository.
2. In Render, create a new Blueprint service from that repository.
3. Render will read `render.yaml` and create the web service automatically.

### Option 2: Manual Web Service setup

If you do not want to use the blueprint file, create a Render Web Service with:

- Build Command:

  ```bash
  pip install -r requirements.txt
  ```

- Start Command:

  ```bash
  python server.py
  ```

- Environment Variable:

  ```text
  MCP_TRANSPORT=streamable-http
  ```

## Render endpoint

After deployment, the MCP HTTP endpoint is:

```text
https://YOUR-RENDER-SERVICE.onrender.com/mcp
```

Render supplies the `PORT` environment variable automatically. This server is already set up to bind to that port and to host `0.0.0.0` when running on Render.

## Notes

- `stdio` mode is for local MCP usage, not for Render web deployment.
- `streamable-http` mode is the correct mode for Render.
- If you rename the service, you do not need to change the code.
