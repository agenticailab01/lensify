# Symbol Micro-Snippets (Phase 5)

The capsule's SYMBOLS section answers "what's the signature of X?" questions
without forcing the agent to open the defining file. For a typical project
this saves ~300-450 tokens per such question.

## What's extracted

Per project tier:

| Tier | Symbols included |
|---|---|
| T1 | 0 (skipped — noise for tiny projects) |
| T2 | top 10 |
| T3 | top 20 |

For each symbol:
- One-line signature (`name(args) -> return_type` or `class Name(Bases)`)
- File path + line number
- Kind: function / method / class

## Ranking

A symbol's rank = the number of other files that import its defining module.
Popular modules surface first; symbols from rarely-imported files are dropped.

This is deliberately simple: it captures ~80% of the practical value at <5% of
the cost of full call-graph analysis. Files that aren't imported by anything
contribute symbols last (often not at all).

## Language coverage

| Language | Method | Accuracy |
|---|---|---|
| Python | stdlib `ast` (full type hints + defaults) | High |
| JavaScript / TypeScript | regex (function decls, classes, arrow consts) | Medium |
| Go | regex (top-level funcs, methods, types) | Medium |

Other languages don't emit symbols. The capsule simply skips the SYMBOLS
section if extraction yields nothing.

## Examples

### Python

Input:
```python
class UserService:
    def find_by_email(self, email: str) -> Optional[User]:
        ...
    def create(self, payload: dict) -> int:
        ...
```

Capsule output:
```markdown
## SYMBOLS

- `class UserService`  (app/domain/user.py:12)
- `UserService.find_by_email(email: str) -> Optional[User]`  (app/domain/user.py:13)
- `UserService.create(payload: dict) -> int`  (app/domain/user.py:16)
```

### TypeScript

Input:
```typescript
export function login(email: string, pw: string): Promise<Token> { ... }
export class AuthCtl extends BaseCtl { ... }
```

Capsule output:
```markdown
- `login(email: string, pw: string) -> Promise<Token>`  (src/auth.ts:8)
- `class AuthCtl extends BaseCtl`  (src/auth.ts:42)
```

### Go

Input:
```go
func (s *Service) Find(id int) (*User, error) { ... }
type Token struct { ... }
```

Capsule output:
```markdown
- `func Service.Find(id int) (*User, error)`  (internal/svc.go:22)
- `type Token struct`  (internal/token.go:5)
```

## How the section matcher uses symbols

When the user's prompt mentions a known symbol name, the section matcher
boosts the SYMBOLS section by +3 (same as a module-name boost). So:

- "what's the signature of `authenticate`?" → SYMBOLS injected
- "how do I call `UserService.find_by_email`?" → SYMBOLS injected
- "what does `login` return?" → SYMBOLS injected

The matcher requires symbol names of ≥3 chars to avoid false-positive matches
on common short tokens.

## Why a separate section (and not just in MODULES)

MODULES gives directory-level orientation ("auth lives in `domain/`"). SYMBOLS
gives call-site-level orientation ("here's the exact signature"). They answer
different questions and have different token costs — keeping them separate
lets the selective-injection hook serve only what the user actually needs.

## What's NOT in the symbols section

- Docstrings (those would explode the budget)
- Method bodies
- Private symbols (`_`-prefixed)
- Symbols from generated code, fixtures, or vendored deps (excluded by walker)
- Symbols that exceed the per-tier cap

If the user needs more depth, they can open the file at the line number the
SYMBOLS entry provides — making the SYMBOLS entry effectively a 30-token
table-of-contents into the codebase's public API.
