# Architecture Decision - Please Review & Approve

## Current State Analysis

### What's Actually Happening Now:

1. **Rules Storage**: 
   - ✅ Rules are in **YAML files** (`rulepacks/euai_core_v1.yaml`)
   - ✅ Rules are **embedded in agent zip** when downloaded
   - ❌ Rules are **NOT in MongoDB**

2. **What Clients Scan**:
   - ✅ Clients provide a **folder** containing their ML project
   - ✅ Scanner looks for **documentation files**:
     - `model_card.json` - Model documentation (Art. 11)
     - `dataset_card.json` - Dataset documentation (Art. 10)
     - `risk_register.yaml` - Risk management (Art. 9)
   - ❌ Scanner does **NOT** scan `.pkl` files or model binaries
   - ✅ Focus is on **compliance documentation**, not model files

3. **MongoDB Usage**:
   - ✅ Stores **scan results** (findings) - optional feature
   - ✅ Used for historical tracking and analytics
   - ❌ Does **NOT** store rules
   - ❌ Does **NOT** distribute rules to clients

4. **Agent Distribution**:
   - ✅ Client downloads agent zip from SaaS
   - ✅ Agent contains embedded rulepack YAML
   - ✅ Agent runs locally (no data leaves client)
   - ✅ Optional: Uploads summary metadata to SaaS

## Your Original Plan vs Current

### Original Plan:
- Rules in MongoDB → Agent fetches from MongoDB → Client scans .pkl files

### Current Implementation:
- Rules in YAML → Agent has embedded rules → Client scans documentation

## Questions for You:

### Question 1: Rules Storage
**Current**: YAML files embedded in agent

**Options:**
- **Option A**: Keep current (YAML embedded) ✅ Recommended for MVP
  - Simpler, no MongoDB dependency for clients
  - Rules versioned with code
  - Privacy-preserving
  
- **Option B**: Switch to MongoDB for rules
  - Rules can be updated without new agent download
  - Centralized rule management
  - Requires MongoDB connection (privacy concern?)

**My Recommendation**: **Option A** for MVP, add MongoDB option later for enterprise

---

### Question 2: What Should Clients Scan?
**Current**: Documentation artifacts only (model_card.json, etc.)

**Options:**
- **Option A**: Keep current (documentation only) ✅ Recommended
  - Privacy-preserving
  - Fast scans
  - Focuses on compliance documentation
  
- **Option B**: Add model file scanning (.pkl, .onnx)
  - More comprehensive
  - Can detect model-specific issues
  - Privacy concerns, slower scans

**My Recommendation**: **Option A** for MVP, add model analysis as premium feature

---

### Question 3: MongoDB Purpose
**Current**: Optional, stores scan results only

**Options:**
- **Option A**: Keep current (results storage only)
  - Simple, optional feature
  - Works without MongoDB
  
- **Option B**: Make MongoDB required
  - Better for multi-tenant SaaS
  - Required for enterprise features
  - More complex deployment

**My Recommendation**: **Option A** for MVP, make required for enterprise tier

---

### Question 4: Tier Limits
**Current**: No limits implemented

**Options:**
- **Option A**: No limits for MVP ✅ Recommended
  - Easier to get users
  - Add limits when you have paying customers
  
- **Option B**: Implement limits now
  - Free: 10 scans/month, basic rules
  - Paid: Unlimited, all rules

**My Recommendation**: **Option A** - No limits for MVP

## My Proposed Architecture (Hybrid)

### For MVP (Now):
1. ✅ Rules: YAML files embedded in agent
2. ✅ What to scan: Documentation artifacts
3. ✅ MongoDB: Optional, for result storage
4. ✅ Tier limits: None

### For Future (Enterprise):
1. MongoDB option for centralized rule management
2. Model file analysis as premium feature
3. MongoDB required for enterprise (multi-tenant)
4. Tier limits based on customer feedback

## Please Confirm:

**Which options do you prefer?**

1. Rules: [ ] Option A (YAML) [ ] Option B (MongoDB)
2. What to scan: [ ] Option A (Documentation) [ ] Option B (Model files too)
3. MongoDB: [ ] Option A (Optional) [ ] Option B (Required)
4. Tier limits: [ ] Option A (None) [ ] Option B (Implement now)

**Once you confirm, I'll implement accordingly and proceed with Phase 2 & 3!**
