"""Select a standalone interactive window for desktop command-line tools."""
import sys


def configure_desktop_backend():
    # PyCharm's plots backend may return from show(block=True) without a
    # standalone window. Choose before importing pyplot or creating figures.
    import matplotlib
    backend = 'MacOSX' if sys.platform == 'darwin' else 'TkAgg'
    try:
        matplotlib.use(backend, force=True)
        # Import now so missing GUI dependencies produce an actionable error.
        from importlib import import_module
        import_module('matplotlib.backends.backend_' + backend.lower())
    except (ImportError, RuntimeError) as exc:
        raise RuntimeError(
            f'Cannot start the {backend} interactive window: {exc}. '
            'Run with the project desktop Python interpreter.'
        ) from exc
    print(f'Interactive window backend: {matplotlib.get_backend()}', flush=True)
