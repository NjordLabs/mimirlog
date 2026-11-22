from typing import Protocol, runtime_checkable

@runtime_checkable
class _Trace(Protocol):
    def get_current_span(self) -> object: ...

@runtime_checkable
class _Span(Protocol):
    def get_span_context(self) -> object: ...

@runtime_checkable
class _SpanContext(Protocol):
    is_valid: bool
    span_id: object

def read_span(module: object) -> object | None: ...
def hex_span_id(context: object) -> str | None: ...
