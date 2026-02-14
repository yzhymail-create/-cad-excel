import os
import sys

try:
    from local_semantic_file_agent.cli import main
except ImportError:  # Allows PyInstaller or direct execution.
    if __package__ is None:
        sys.path.append(os.path.dirname(os.path.dirname(__file__)))
        from local_semantic_file_agent.cli import main  # type: ignore[no-redef]
    else:
        raise


if __name__ == "__main__":
    main()
