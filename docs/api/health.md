# Health API

## `GET /health`

Server health check. Returns service status, name, and version.

**Authentication:** None

### Response

```json
{
  "status": "healthy",
  "service": "SwadeshAI Backend",
  "version": "1.0.0"
}
```
