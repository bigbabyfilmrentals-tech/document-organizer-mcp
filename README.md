# Document Organizer MCP

This is a starter MCP server you can plug into an agent that needs to do more with documents than basic chat alone.

It gives your agent a few practical abilities:

- list documents inside a chosen folder
- inspect document metadata and previews
- extract text from common file types
- search across many documents at once
- summarize the overall collection
- propose cleaner filenames from document content
- move files safely inside the allowed document root
- optionally search and read Google Drive files with an OAuth token

## Why this is a good first custom MCP

You said you have never built one before, so this project stays small on purpose:

- one server file
- one configurable document root
- a handful of tools that are easy to test
- no database, auth flow, or cloud deployment required for version one

Once this works, you can keep adding richer behaviors like tagging, rename suggestions, duplicate detection, filing rules, Drive integration, or OCR.

## Important for ChatGPT Business

ChatGPT Business can connect only to a **remote** MCP server, not one running only on your laptop or inside this workspace.

That is why this project now includes remote hosting files:

- `Dockerfile`
- `render.yaml`
- `requirements.txt`

This starter is set up for a **simple first deployment without authentication**. That is the easiest way to get unstuck, but it also means:

- only upload non-sensitive test documents at first
- keep documents inside the `data/` folder
- do not point `DOC_ROOT` at your whole machine or workspace

Once you are comfortable, the next upgrade should be adding authentication.

## Supported file types

- `.txt`
- `.md`
- `.json`
- `.csv`
- `.pdf`
- `.docx`
- `.xlsx`

## Project layout

```text
document-organizer-mcp/
├── pyproject.toml
├── README.md
└── server.py
```

## Setup

From this folder:

```bash
cd /workspace/document-organizer-mcp
uv sync
```

Pick the folder your agent should be allowed to inspect. For example:

```bash
export DOC_ROOT=/workspace/document-organizer-mcp/data
```

Optional: restrict which extensions are searchable.

```bash
export DOC_EXTENSIONS=.pdf,.docx,.md,.txt
```

## Run locally

For local development with the MCP inspector:

```bash
uv run mcp dev server.py
```

For direct stdio use:

```bash
uv run python server.py
```

For the remote HTTP shape that ChatGPT expects:

```bash
HOST=0.0.0.0 PORT=8000 uv run python server.py
```

The MCP endpoint will be:

```text
http://localhost:8000/mcp
```

## Available tools

### `healthcheck`
Returns the active document root and allowed extensions.

### `list_documents`
Shows files under the document root.

Example:

```json
{
  "subdir": "contracts",
  "limit": 25
}
```

### `inspect_document`
Returns metadata and a short preview for a single file.

### `extract_document_text`
Pulls document text into the agent context.

### `search_documents`
Searches across documents and returns snippets around each hit.

### `summarize_collection`
Returns collection-level stats so the agent can get oriented quickly.

### `propose_rename`
Suggests a better filename using the first meaningful line of extracted text and a detected date when available.

### `move_document`
Moves a file inside `DOC_ROOT`. It defaults to `dry_run=true`, which is the safer way to start.

Example:

```json
{
  "source_path": "inbox/scan-001.pdf",
  "destination_dir": "contracts/2026",
  "new_name": "2026-05-22 Master Services Agreement.pdf",
  "dry_run": true
}
```

### `drive_status`
Checks whether the optional Google Drive bridge has been configured.

### `drive_search_files`
Searches Google Drive through the Drive API. The `query` field uses normal Drive API query syntax.

Example:

```json
{
  "query": "name contains 'invoice' and 'root' in parents",
  "page_size": 10
}
```

### `drive_get_file`
Fetches metadata for a single Drive file.

### `drive_extract_text`
Exports or downloads text from Drive files. For Google Docs and Slides it uses plain text export. For Google Sheets it uses CSV export of the first sheet.

### `search`
A ChatGPT-friendly search entry point. It returns search results in the shape OpenAI documents for MCP search tools.

### `fetch`
A ChatGPT-friendly fetch entry point. It returns the full contents of a selected search result item.

## Google Drive setup

The Drive bridge is optional. It uses a bearer token in:

```bash
export GOOGLE_DRIVE_ACCESS_TOKEN=your_access_token_here
```

For a first build, the simplest path is:

1. Create a Google Cloud project.
2. Enable the Google Drive API.
3. Create OAuth client credentials.
4. Generate a user access token with a Drive scope such as `drive.readonly` or `drive.file`.
5. Pass that access token into the MCP host as `GOOGLE_DRIVE_ACCESS_TOKEN`.

This starter keeps auth intentionally simple so you can get the bridge working before you build token refresh or a full sign-in flow.

## Deploy to Render

This is the easiest path I recommend for a first deployment.

### 1. Put only safe test files in `data/`

Use this folder:

```text
document-organizer-mcp/data/
```

Do not deploy your full workspace as a public no-auth MCP.

### 2. Put this project in a GitHub repo

Render deploys most smoothly from GitHub. Create a repo and upload the contents of `document-organizer-mcp/`.

### 3. Create a new Render Web Service

In Render:

1. Click `New +`
2. Choose `Web Service`
3. Connect your GitHub repo
4. Render should detect the included `Dockerfile`

### 4. Set environment variables in Render

Use these values:

- `HOST` = `0.0.0.0`
- `PORT` = `8000`
- `DOC_ROOT` = `/app/data`

Optional:

- `DOC_EXTENSIONS` = `.pdf,.docx,.md,.txt,.xlsx,.csv,.json`
- `GOOGLE_DRIVE_ACCESS_TOKEN` = your temporary OAuth access token if you want Drive read access

### 5. Deploy

After deploy finishes, your MCP endpoint will look like:

```text
https://your-service-name.onrender.com/mcp
```

Save that URL. That is what ChatGPT Business will connect to.

## Add it in ChatGPT Business

As of May 27, 2026, ChatGPT Business uses developer mode and remote MCP apps for this flow.

### 1. Enable developer mode

In ChatGPT web:

1. Open `Workspace Settings`
2. Go to `Permissions & Roles`
3. Find `Connected Data Developer mode / Create custom MCP connectors`
4. Turn it on for yourself

On Business, only admins or owners can do this.

### 2. Create the app

In ChatGPT web:

1. Open `Workspace Settings`
2. Go to `Apps`
3. Click `Create`
4. Choose the option to add a custom MCP app
5. Paste your remote MCP URL, for example:

```text
https://your-service-name.onrender.com/mcp
```

### 3. Test privately

Start a new chat and attach or invoke the draft app. Try prompts like:

- `Summarize the document collection available in this app`
- `Find documents about invoices`
- `Suggest cleaner names for the available files`

### 4. Publish

When it looks good:

1. Go back to `Workspace Settings`
2. Open `Apps`
3. Find the draft
4. Click `Publish`

Business note:

- published apps currently are not edited in place
- if you change tools or metadata later, recreate and republish

## How I would use this with your document organizer agent

A good first workflow for the agent is:

1. `summarize_collection` to understand the folder.
2. `list_documents` to discover likely targets.
3. `inspect_document` or `extract_document_text` to read them.
4. `propose_rename` to produce cleaner names.
5. `move_document` with `dry_run=true` first.
6. `move_document` with `dry_run=false` once the plan looks right.
7. `drive_search_files` and `drive_extract_text` when you want the same agent to reach into Drive.
8. `search` and `fetch` when ChatGPT wants a connector-style search/fetch flow.

## Good next upgrades

If you want your document organizer agent to become genuinely useful, these are the next features I would add:

1. `suggest_folders_for_document`
   Use file content plus filename patterns to recommend where a document belongs.
2. `find_duplicates`
   Detect repeated files by hash, name similarity, or matching extracted text.
3. `tag_document`
   Save lightweight metadata in a sidecar JSON file.
4. `index_cache`
   Cache extracted text so large collections search faster.
5. `oauth_refresh_flow`
   Replace the one-off Drive access token with a renewable sign-in flow.
6. `drive_move_or_label`
   Extend the Drive bridge from read-only access into organization actions.

## Notes on the MCP stack

This starter uses the official Python MCP SDK and `FastMCP`, which is the current stable path in the official Python SDK documentation as of May 27, 2026.
