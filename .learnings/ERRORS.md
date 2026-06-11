# ERRORS.md — 错误日志
<!-- Format: [ERR-YYYYMMDD-XXX] | Log command failures, exceptions, unexpected behavior -->


## [ERR-20260316-001] aisa-twitter-api

**Logged**: 2026-03-16T02:50:00Z
**Priority**: high
**Status**: resolved
**Area**: config

### Summary
AISA Twitter API 余额耗尽，所有 Twitter 搜索返回 401/余额不足

### Error
```
AISA API 余额耗尽（2026-03-14 一天 20+ 次搜索耗光）
```

### Context
- API key: sk-d2n3PIPWBOc3VTgqHuqvtmTaSZ5JtolHBnUAaUrAZgTjst41
- 充值入口: https://api.aisa.one
- 建议充值金额: $5-10

### Suggested Fix
充值 AISA API 余额后恢复正常

### Metadata
- Reproducible: no（充值后解决）
- Related Files: TOOLS.md, HEARTBEAT.md

---
