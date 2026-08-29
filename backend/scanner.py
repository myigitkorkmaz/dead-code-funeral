import os
import shutil
import tempfile
import git
import vulture


def clone_repo(github_url: str) -> str:
    """Clone a GitHub repo into a temp directory and return the path."""
    temp_dir = tempfile.mkdtemp(prefix="dead_code_funeral_")
    git.Repo.clone_from(github_url, temp_dir)
    return temp_dir


def scan_for_dead_code(repo_path: str) -> list[dict]:
    """
    Run vulture on all Python files in repo_path and return a list of dead
    code items. Each item is a dict with keys:
        name     – identifier name
        filename – path to the file (relative to repo_path)
        line     – line number where the item is defined
        type     – human-readable kind (e.g. "unused function")
        size     – number of lines the item spans (1 when unknown)
    """
    v = vulture.Vulture()

    py_files = [
        os.path.join(root, f)
        for root, _, files in os.walk(repo_path)
        for f in files
        if f.endswith(".py")
    ]

    if not py_files:
        return []

    v.scavenge(py_files)

    results = []
    for item in v.get_unused_code():
        results.append(
            {
                "name": item.name,
                "filename": os.path.relpath(item.filename, repo_path),
                "line": item.first_lineno,
                "type": f"unused {item.typ}",
                "size": item.size if item.size is not None else 1,
            }
        )

    return results


def cleanup(repo_path: str) -> None:
    """Delete the cloned repo temp directory."""
    shutil.rmtree(repo_path, ignore_errors=True)
