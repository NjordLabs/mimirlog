# mimirlog

JSON logging for Python 3.13 services. Each record is one JSON line.
Mapping keys named `password`, `token`, `secret`, or `authorization`
are written as `***`. A correlation id comes from a context variable.

The package is not on PyPI. Install the release tag:

```bash
pip install "mimirlog @ git+https://github.com/NjordLabs/mimirlog.git@v0.1.0"
```

Requires Python 3.13. Named loggers are cached with
[pymjolnir](https://github.com/NjordLabs/pymjolnir).

```python
from mimirlog import bind, configure, get_logger

configure()
with bind("request-1"):
    get_logger("app").info({"event": "ready", "password": "secret"})
```

`log_call` and `benchmark` record the call and its duration. They do
not record arguments. `current_span_id` returns a hex id when
OpenTelemetry is installed, and `None` when it is not.

Source and issues: [NjordLabs/mimirlog](https://github.com/NjordLabs/mimirlog)
