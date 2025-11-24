# AGENTS.md - Unified AI Code Assistant Guidelines v3.0

> **Scope**: Comprehensive operational guidelines for AI code assistants covering strategic selection, tactical implementation, and enterprise compliance. Written for AI assistants, not human contributors.

---

## Table of Contents
1. [Core Principles](#core-principles)
2. [Dynamic Model Selection](#dynamic-model-selection)
3. [Context & Scope Management](#context--scope-management)
4. [Security-First Development](#security-first-development)
5. [Output Standards](#output-standards)
6. [Quality Gates & Validation](#quality-gates--validation)
7. [Testing Framework](#testing-framework)
8. [Performance & Scalability](#performance--scalability)
9. [Compliance & Governance](#compliance--governance)
10. [Language/Stack Profiles](#languagestack-profiles)
11. [Documentation & Change Tracking](#documentation--change-tracking)
12. [Human-AI Collaboration](#human-ai-collaboration)
13. [Operational Metadata](#operational-metadata)
14. [Templates & Examples](#templates--examples)

---

## Core Principles

1. **Dynamic Intelligence**: Select optimal model based on task complexity and domain requirements
2. **Security-First**: Apply multi-stage security validation before functional implementation
3. **Production-Ready**: Generate immediately deployable, enterprise-grade code
4. **Deterministic Excellence**: Ensure reproducible outputs through fixed configurations
5. **Context-Aware**: Adapt to project conventions while maintaining quality standards
6. **Compliance-Ready**: Integrate regulatory requirements into development workflow
7. **Human-Centric**: Design for effective human-AI collaboration and review processes
8. **Language**: This App uses Spanish as default language for variable names, documents and comments

---

## Dynamic Model Selection

### Task-Appropriate Model Assignment
- **Complex Architecture/Reasoning**: Use highest-capability model (Claude 4 Opus, GPT-5.1-Codex-Max)
- **General Development**: Cost-effective models (GPT-4.1, Claude 4 Sonnet)
- **Specialized Logic**: Reasoning-optimized models (O3 or similar newer model)  
- **Security-Critical**: Models with verified security training
- **Legacy Codebase**: Models trained on specific language versions/frameworks

### Configuration Standards
```yaml
model_config:
  primary_model: "claude-4-opus@2025-09-01"
  fallback_models: ["gpt-5.1", "claude-4-sonnet"]
  determinism:
    seed: 42
    temperature: 0.0-0.1  # 0.0 for code, 0.1 for problem-solving
    top_p: 1.0
  quality_threshold: 0.95
  max_retries: 3
```

**Record in all outputs**: Model version, seed, configuration, fallbacks used

---

## Context & Scope Management

### Explicit Constraint Adherence
- Follow specified: language, runtime version, framework, style, output format
- Work only with provided/confirmed files - never invent unseen components
- State minimal assumptions explicitly and proceed deterministically
- Maintain conversation context and decision rationale

### Assumption Protocol (ASK/ASSUME/PROCEED)
1. **Critical missing info**: State explicit assumptions, keep minimal and reversible
2. **Public API impact**: Propose options A/B with rationale, choose one
3. **Security implications**: Default to secure patterns, flag for human review

---

## Security-First Development

### Multi-Stage Security Validation
**Stage 1 - Requirements Analysis**:
- Identify security-sensitive operations
- Apply threat modeling to generated components
- Select secure-by-default patterns and libraries

**Stage 2 - Code Generation**:
- Generate functional code with security placeholders
- Apply security hardening as separate transformation
- Include security-focused comments explaining sensitive operations

**Stage 3 - Validation**:
- Run SAST analysis on generated code
- Validate against OWASP Top 10
- Generate security-focused test cases

### Mandatory Security Practices
- **No secrets**: Use placeholders, environment variables, secure configuration
- **Input validation**: Validate all external inputs, fail fast with clear errors
- **Database security**: Parameterized queries, ORM patterns, migration safety
- **Access control**: Principle of least privilege, role-based permissions
- **Audit trails**: Log security-relevant operations without leaking sensitive data

### Compliance Integration
- **HIPAA**: Health data protection patterns, audit logging, access controls
- **GDPR**: Data minimization, consent management, deletion capabilities  
- **SOX**: Financial audit trails, separation of duties, change management
- **PCI-DSS**: Payment data security, tokenization, secure transmission

---

## Output Standards

### Default Format: Enhanced Unified Diff
```yaml
---
META:
  task_id: "stable-id-{{timestamp}}"
  model: "claude-4-opus@2025-09-01"
  seed: 42
  complexity_score: 0.7  # 0-1 scale
  inputs:
    files: ["src/foo.py", "tests/test_foo.py"]
    context: ["existing API patterns", "security requirements"]
  assumptions:
    - "Input validation follows existing patterns"
    - "Database migrations are backwards compatible"
  outputs:
    format: "unified-diff"
    security_validated: true
    compliance_frameworks: ["SOX", "GDPR"]
  quality_gates_expected:
    build: pass
    lint: pass  
    typecheck: pass
    tests: pass
    security_scan: pass
    coverage_touched_lines: ">=85%"
  performance_impact:
    time_complexity: "O(n log n)"
    memory_usage: "+15% baseline"
    cache_hit_ratio: ">=90%"
  risks:
    - "Breaking change for API v1.x clients"
    - "Potential performance regression for n>10^6"
  human_review_required:
    - "Database schema changes"
    - "Security-sensitive authentication logic"
  commands:
    setup: "make install-dev"
    validate: "make lint && make typecheck && make test && make security-scan"
    deploy: "make deploy-staging"
---
```

### Alternative: Structured JSON Edit Plan
```json
{
  "edits": [
    {
      "path": "string",
      "action": "create|modify|delete|rename",
      "before": "optional string",
      "after": "optional string",
      "rationale": "security hardening for user input",
      "impact": "breaking|compatible|enhancement",
      "review_required": boolean
    }
  ],
  "meta": {
    "model": "claude-4-opus@2025-09-01",
    "seed": 42,
    "security_validated": true,
    "compliance_check": "passed",
    "performance_impact": "minimal"
  },
  "validation": {
    "commands": ["make validate"],
    "expected": {"all_gates": "pass"},
    "human_review": ["security logic", "database changes"]
  }
}
```

---

## Quality Gates & Validation

### Mandatory Quality Pipeline
1. **Build**: Project compiles/builds without errors
2. **Format**: Code passes formatter with zero style violations  
3. **Lint**: Passes linter with zero new warnings (project-specific rules)
4. **Type Safety**: Strong type checking passes (TypeScript/MyPy/etc.)
5. **Security**: SAST analysis passes, no critical vulnerabilities
6. **Tests**: All existing tests pass, new tests achieve ≥85% coverage
7. **Performance**: No regression on key performance metrics
8. **Documentation**: Public APIs documented, breaking changes noted

### Validation Commands Template
```bash
# Environment Setup
make install-dev || npm install --dev || pip install -r requirements-dev.txt

# Quality Pipeline
make format-check || prettier --check . || black --check .
make lint || eslint . || ruff check .
make typecheck || tsc --noEmit || mypy .
make security-scan || npm audit || safety check
make test || npm test || pytest
make coverage-report

# Performance Validation (if applicable)  
make benchmark-critical-path
```

---

## Testing Framework

### Comprehensive Test Generation Strategy
- **Unit Tests**: Fast, isolated, mocked dependencies
- **Property-Based Tests**: Use Hypothesis (Python), fast-check (JS), QuickCheck (Haskell)
- **Integration Tests**: Cross-module behavior, real dependencies
- **Security Tests**: Input validation, authentication, authorization edge cases
- **Performance Tests**: Load testing, resource usage, caching effectiveness

### Test Coverage Requirements
- **Critical paths**: 95% statement + branch coverage
- **General code**: 85% statement coverage  
- **Generated functions**: 100% coverage with edge cases
- **Security logic**: Explicit negative test cases
- **API endpoints**: Happy path + error scenarios

### Example Test Structure
```python
# Property-based testing example
from hypothesis import given, strategies as st

@given(st.lists(st.integers()))
def test_sum_properties(values):
    """Test mathematical properties of sum function."""
    result = sum_iter(values)
    assert result == sum(values)  # Reference implementation
    assert sum_iter([]) == 0      # Identity
    assert sum_iter([x]) == x for x in values  # Single element
```

---

## Performance & Scalability

### Performance-Aware Code Generation
- **Algorithm Selection**: Choose asymptotically optimal algorithms for expected data sizes
- **Caching Strategy**: Multi-tier caching (in-memory, distributed, persistent)
- **Resource Management**: Bounded memory usage, connection pooling, graceful degradation
- **Monitoring Integration**: Performance metrics, alerting thresholds, profiling hooks

### Scalability Targets
- **Response Times**: <100ms cached, <500ms uncached, <2s complex operations
- **Throughput**: Handle 10x current load with horizontal scaling
- **Resource Usage**: Memory growth O(log n) with dataset size
- **Cache Performance**: >90% hit ratio for frequently accessed data

### Performance Testing Integration
```python
# Micro-benchmark template
import timeit
import psutil
import memory_profiler

@memory_profiler.profile
def benchmark_critical_function():
    """Benchmark with memory profiling."""
    start_time = timeit.default_timer()
    result = critical_function(test_data)
    end_time = timeit.default_timer()
    
    assert end_time - start_time < 0.5  # 500ms SLA
    return result
```

---

## Compliance & Governance

### Regulatory Framework Integration
**Healthcare (HIPAA)**:
- PHI data handling patterns
- Access logging and audit trails  
- Encryption at rest and in transit
- Patient consent management

**Financial (SOX)**:
- Change management workflows
- Separation of duties in code reviews
- Audit trail for all modifications
- Data integrity controls

**Privacy (GDPR)**:
- Data minimization patterns
- Consent collection and management
- Right to deletion implementation
- Cross-border data transfer controls

### AI Governance Requirements  
- **Bias Detection**: Algorithmic fairness validation for decision-making code
- **Explainability**: Generate documentation explaining AI-assisted decisions
- **Human Oversight**: Flag complex logic requiring human domain expert review
- **Audit Trail**: Complete traceability of AI-generated code and rationale

---

## Language/Stack Profiles

### Python (≥3.11)
**Tools**: `ruff` (lint/format), `mypy --strict` (types), `pytest` (tests), `uv` (deps)
```bash
# Validation Pipeline
ruff format --check . && ruff check .
mypy --strict .
pytest --cov=src --cov-report=term-missing
safety check
bandit -r src/
```
**Patterns**: Prefer `pathlib`, `typing.Protocol`, dataclasses/pydantic, async/await

### TypeScript/JavaScript (Node LTS)
**Tools**: `eslint`, `prettier`, `typescript`, `vitest`/`jest`, `npm audit`
```bash
# Validation Pipeline  
prettier --check .
eslint .
tsc --noEmit
npm test
npm audit --audit-level=moderate
```
**Patterns**: Strict TS config, no `any`, proper error handling, tree-shaking friendly

### Go (≥1.22)
**Tools**: `gofmt`, `golangci-lint`, `go test`, `gosec`
```bash
# Validation Pipeline
golangci-lint run
go test -race -cover ./...
gosec ./...
go mod verify
```
**Patterns**: Context-aware I/O, proper error handling, no global state

### Java (≥21)  
**Tools**: Maven/Gradle, Checkstyle, SpotBugs, Error Prone, JUnit
```bash
# Validation Pipeline (Maven)
mvn clean verify -Dcheckstyle.failsOnError=true
mvn spotbugs:check
mvn test
```
**Patterns**: Records, sealed classes, try-with-resources, minimal reflection

### Rust (stable)
**Tools**: `cargo fmt`, `cargo clippy`, `cargo test`, `cargo audit`
```bash
# Validation Pipeline
cargo fmt --check
cargo clippy -- -D warnings  
cargo test
cargo audit
```
**Patterns**: Zero-cost abstractions, ownership patterns, error propagation

---

## Documentation & Change Tracking

### Living Documentation Standards
- **API Documentation**: OpenAPI 3.0+ with working examples, tested against implementation
- **Architectural Decisions**: ADRs for significant design choices with rationale
- **Security Documentation**: Threat models, security controls, incident response procedures
- **Deployment Guides**: Environment-specific configuration, rollback procedures

### Change Management
```markdown
# CHANGELOG.md entry template
## [1.2.0] - 2025-09-23
### Added
- User authentication API with JWT tokens [SECURITY]
- Rate limiting middleware for API endpoints [PERFORMANCE]

### Changed  
- Database connection pooling from 10 to 50 connections [BREAKING]
- Migration from REST to GraphQL for user queries [BREAKING]

### Security
- Fixed SQL injection vulnerability in user search (CVE-2025-1234)
- Updated dependencies with known security issues

### Migration Guide
- Update client applications to use new authentication headers
- Database migration required: `npm run migrate:up`
- Rollback available: `npm run migrate:down`
```

---

## Human-AI Collaboration

### Code Review Integration
- **AI Attribution**: Clear comments marking AI-generated code sections
- **Decision Rationale**: Explain complex implementation choices
- **Review Checklists**: Generate human review points for critical sections
- **Feedback Loop**: Incorporate human corrections into future generations

### Collaboration Patterns
```python
# AI-generated code with human collaboration markers
def process_user_data(user_input: str) -> ProcessedData:
    """
    Process user input with validation and sanitization.
    
    AI-GENERATED: Core validation logic
    HUMAN-REVIEW-REQUIRED: Business rule validation at line 45
    SECURITY-CRITICAL: Input sanitization logic
    """
    # AI: Input validation
    if not user_input or len(user_input) > 1000:
        raise ValidationError("Invalid input length")
    
    # AI: Sanitization  
    sanitized = sanitize_input(user_input)
    
    # TODO: HUMAN - Add business-specific validation rules
    # This requires domain knowledge about user data constraints
    
    return ProcessedData(sanitized)
```

---

## Operational Metadata

### Required Output Metadata
All AI assistant outputs must include:
```yaml
operational_metadata:
  model_info:
    primary: "claude-4-opus@2025-09-01"
    fallbacks_used: []
    configuration: {seed: 42, temperature: 0.0}
    
  quality_assurance:
    security_validated: true
    compliance_frameworks: ["GDPR", "SOX"]
    test_coverage: 87.3
    performance_impact: "minimal"
    
  collaboration:
    human_review_points: ["authentication logic", "database schema"]
    estimated_review_time: "45 minutes"
    complexity_score: 0.7
    
  traceability:
    prompt_version: "3.0"
    generation_timestamp: "2025-09-23T10:30:00Z"
    conversation_context: "feature-auth-system"
```

---

## Templates & Examples

### Response Template
```
META: [YAML metadata block]
PLAN: [3-7 bullet rationale and steps] 
SECURITY: [Security analysis and validation]
PERFORMANCE: [Performance considerations and benchmarks]
COMMANDS: [Exact validation pipeline commands]
TESTS: [Generated test cases with fixtures]
DOCUMENTATION: [Updated docs, changelogs, migration guides]
DIFF: [Unified diff or JSON edit plan]
COLLABORATION: [Human review requirements and checklists]
ROLLBACK: [Rollback procedures and risk mitigation]
```

### CI/CD Integration Example
```yaml
# .github/workflows/ai-generated-validation.yml
name: AI-Generated Code Validation
on: 
  pull_request:
    paths: ['**/*AI-GENERATED*', '**/*ai-gen*']

jobs:
  enhanced-validation:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup Environment
        run: make install-dev
      - name: Security Scan  
        run: make security-scan
      - name: Performance Baseline
        run: make benchmark-critical-path
      - name: Compliance Check
        run: make compliance-validation
      - name: Human Review Required
        if: contains(github.event.pull_request.body, 'HUMAN-REVIEW-REQUIRED')
        run: echo "::warning::Human review required for security-critical changes"
```

---

**End of Unified AGENTS.md v3.0**

*This document combines strategic AI model selection, tactical implementation guidance, enterprise compliance requirements, and human-AI collaboration patterns into a comprehensive operational framework for AI code assistants.*