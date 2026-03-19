# Architecture Clarification - Current vs Original Plan

## Your Original Plan

**Original Idea:**
- Rules stored in MongoDB (source of truth)
- Clients download agent wrapper
- Agent points to MongoDB to get rules
- Client provides their ML project folder (with .pkl files)
- Agent scans and generates results based on tier limits

## Current Implementation

**What's Actually Happening:**

### Rules Storage:
- ✅ Rules are stored in **YAML files** (`rulepacks/euai_core_v1.yaml`)
- ✅ Rules are **packaged with the agent** (embedded)
- ❌ Rules are **NOT** stored in MongoDB
- ✅ MongoDB is used for **storing scan results** only (optional)

### What Clients Scan:
- ✅ Clients provide a **folder/directory** containing their ML project
- ✅ Scanner looks for **documentation artifacts** (not model files):
  - `model_card.json` - Model documentation
  - `dataset_card.json` - Dataset documentation  
  - `risk_register.yaml` - Risk management
- ❌ Scanner does **NOT** scan `.pkl` files or model binaries
- ✅ Scanner scans **compliance documentation** only

### Agent Distribution:
- ✅ Client downloads agent zip from SaaS dashboard
- ✅ Agent contains:
  - Rulepack YAML files (embedded)
  - Scanner code
  - Evaluators
  - Report generators
- ✅ Agent runs **locally** (no data leaves client system)
- ✅ Optional: Agent can upload summary to SaaS (metadata only)

### MongoDB Usage:
**Current Purpose:**
- Store scan results (findings) for historical tracking
- Optional feature (can run without MongoDB)
- Used for analytics and report archival

**NOT Used For:**
- ❌ Storing rules (rules are in YAML files)
- ❌ Rule distribution (rules are embedded in agent)

## Questions for You:

### 1. MongoDB for Rules?
**Option A: Keep current (YAML files)**
- ✅ Simpler deployment
- ✅ No MongoDB dependency for clients
- ✅ Rules versioned with code
- ❌ Rule updates require new agent download

**Option B: MongoDB for rules (original plan)**
- ✅ Rules can be updated without new agent
- ✅ Centralized rule management
- ✅ Can push rule updates to clients
- ❌ Requires MongoDB connection
- ❌ More complex architecture
- ❌ Privacy concerns (client connects to your DB)

**Recommendation**: Keep YAML for MVP, add MongoDB option later for enterprise

### 2. What Should Clients Scan?
**Current**: Documentation artifacts (model_card.json, etc.)

**Options:**
- **Option A: Keep current** - Scan documentation only
  - ✅ Privacy-preserving (no model files scanned)
  - ✅ Fast scans
  - ✅ Focuses on compliance documentation
  
- **Option B: Scan model files too** - Analyze .pkl/.onnx files
  - ✅ More comprehensive analysis
  - ✅ Can detect model-specific issues
  - ❌ Privacy concerns
  - ❌ Slower scans
  - ❌ Requires model loading libraries

**Recommendation**: Keep current (documentation only) for MVP, add model analysis as premium feature

### 3. Tier Limits?
**Current**: No tier limits implemented

**Options:**
- **Option A: Rule limits** - Free tier gets X rules, paid gets all
- **Option B: Scan frequency** - Free: monthly, Paid: unlimited
- **Option C: Features** - Free: basic reports, Paid: advanced analytics
- **Option D: No limits** - Keep free for MVP, add limits later

**Recommendation**: Option D for MVP, add limits when you have paying customers

## Proposed Architecture (Hybrid Approach)

### For MVP (Current):
1. **Rules**: YAML files packaged with agent ✅
2. **What to scan**: Documentation artifacts ✅
3. **MongoDB**: Optional, for result storage only ✅
4. **Tier limits**: None for MVP ✅

### For Future (Enterprise):
1. **Rules**: MongoDB option for centralized management
2. **What to scan**: Add model file analysis as premium feature
3. **MongoDB**: Required for enterprise (multi-tenant)
4. **Tier limits**: Implement based on customer feedback

## My Recommendation

**Keep current architecture for MVP** because:
- ✅ Simpler to deploy and maintain
- ✅ No external dependencies for clients
- ✅ Privacy-preserving (local-first)
- ✅ Faster to market

**Add MongoDB option later** when you have:
- Enterprise customers who want centralized rule management
- Need for rule updates without agent re-download
- Multi-tenant requirements

**What do you think?** Should we:
1. Keep current (YAML rules, documentation scanning)?
2. Switch to MongoDB for rules?
3. Add model file scanning?
4. Implement tier limits now?

Let me know your preference and I'll implement accordingly!
