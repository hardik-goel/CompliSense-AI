# Redundant Files to Remove

## Files Safe to Delete:

1. **agent/api.py** - Simple duplicate of agent/api_handlers.py
   - `agent/api_handlers.py` is more complete and used by `agent/agent_main.py`
   - `agent/api.py` is not imported anywhere

2. **server/saas_api.py** - Duplicate SaaS API
   - `saas/app/main.py` is the current SaaS server
   - `server/saas_api.py` is not imported anywhere

3. **server/auth.py** - Legacy auth module
   - `saas/app/auth.py` is the current auth implementation
   - `server/auth.py` is not imported anywhere

## Keep These:

- `agent/api_handlers.py` - Used by agent_main.py
- `saas/app/main.py` - Main SaaS server
- `saas/app/auth.py` - Current auth implementation

## Action:

Run these commands to remove redundant files:
```bash
rm agent/api.py
rm server/saas_api.py
rm server/auth.py
```
