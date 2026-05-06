# cassen-mcp-image-gen

MCP server exposing a `generate_image` tool. Calls the free
[Pollinations.ai](https://pollinations.ai) endpoint (Flux model by default) and
writes the resulting PNG to a path you specify.

Built so Claude Code (and any other MCP client) can ask for a logo or image and
have the file land directly in the workspace, the way an Obsidian plugin
extends a vault.

## Install

```sh
cd mcp-image-gen
npm install
```

## Register with Claude Code

```sh
claude mcp add cassen-image node -- "C:\\Users\\HP\\Cassen\\mcp-image-gen\\src\\index.mjs"
```

Then **restart Claude Code**. After restart, the `generate_image` and
`build_image_url` tools are available to the assistant.

If you prefer a config file over the CLI, add to your Claude Code config
(`~/.claude.json` or wherever your installation reads from):

```json
{
  "mcpServers": {
    "cassen-image": {
      "command": "node",
      "args": ["C:\\Users\\HP\\Cassen\\mcp-image-gen\\src\\index.mjs"]
    }
  }
}
```

## Tools

### `generate_image`

| param         | type    | required | default     | notes                               |
|---------------|---------|----------|-------------|-------------------------------------|
| `prompt`      | string  | yes      | —           | Be detailed for realistic 3D output |
| `output_path` | string  | yes      | —           | Absolute or cwd-relative            |
| `width`       | integer | no       | 1024        | 256–2048                            |
| `height`      | integer | no       | 1024        | 256–2048                            |
| `model`       | string  | no       | `flux`      | `flux`, `turbo`, etc.               |
| `seed`        | integer | no       | random      | Set for reproducibility             |
| `enhance`     | boolean | no       | false       | Pollinations rewrites the prompt    |

### `build_image_url`

Same params (minus `output_path`). Returns the Pollinations URL without
downloading — handy if you want to embed the URL in a Markdown file or share
the source link.

## Swap the backend

The Pollinations endpoint is free and unauthenticated, but quality is capped.
To switch to a paid provider (Replicate, Fal, Together, OpenAI Images, etc.),
edit `buildUrl` and `fetchImage` in `src/index.mjs` to call the new endpoint
and add an env-var-driven API key.

## Standalone test

```sh
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | node src/index.mjs
```

You should see the tool list as a JSON-RPC response on stdout.
