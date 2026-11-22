# mimirlog

Structured logging for Python 3.13 services. Records are JSON lines.
Secret mapping keys are redacted. A correlation id is taken from a
context variable.

```bash
pip install mimirlog
```

This repository is the source until the package is published. The
named-logger cache uses
[pymjolnir](https://github.com/NjordLabs/pymjolnir) at commit
`aa9a2ee85fafd2102bfdb0a5b3bb97d194715d20`.

```python
from mimirlog import bind, configure, get_logger

configure()
with bind("request-1"):
    get_logger("app").info({"event": "ready", "password": "secret"})
```

`password`, `token`, `secret`, and `authorization` are written as
`***`. Arguments of `log_call` and `benchmark` are not logged.
