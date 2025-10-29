from contextlib import contextmanager
from sqlalchemy.orm import sessionmaker, scoped_session, Session
from .extensions import ENGINE

_session_factory = None
_scoped = None


def init_session_factory():
    global _session_factory, _scoped
    if ENGINE is None:
        raise RuntimeError("ENGINE is not set. Pass an Engine to create_app(engine).")
    _session_factory = sessionmaker(bind=ENGINE, autoflush=False, expire_on_commit=False)
    _scoped = scoped_session(_session_factory)


def get_scoped_session() -> Session:
    if _scoped is None:
        init_session_factory()
    return _scoped


@contextmanager
def session_scope() -> Session:
    """Provide a transactional scope around a series of operations."""
    s = get_scoped_session()
    try:
        yield s
        s.commit()
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()
