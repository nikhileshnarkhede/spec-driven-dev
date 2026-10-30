"""Print the public interface of Python files — signatures only, no bodies or constant values: interface_surface.py FILE..."""
import ast
import sys
from pathlib import Path


def signature(node: ast.FunctionDef | ast.AsyncFunctionDef, indent: str = "") -> str:
    keyword = "async def" if isinstance(node, ast.AsyncFunctionDef) else "def"
    returns = f" -> {ast.unparse(node.returns)}" if node.returns else ""
    return f"{indent}{keyword} {node.name}({ast.unparse(node.args)}){returns}"


def is_public(name: str) -> bool:
    return not name.startswith("_") or name == "__init__"


def surface(tree: ast.Module) -> list[str]:
    lines = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and is_public(node.name):
            lines.append(signature(node))
        elif isinstance(node, ast.ClassDef) and is_public(node.name):
            bases = ", ".join(ast.unparse(base) for base in node.bases)
            lines.append(f"class {node.name}({bases}):" if bases else f"class {node.name}:")
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and is_public(item.name):
                    lines.append(signature(item, indent="    "))
                elif isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                    lines.append(f"    {item.target.id}: {ast.unparse(item.annotation)}")
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id.isupper():
            lines.append(f"{node.target.id}: {ast.unparse(node.annotation)}")
        elif isinstance(node, ast.Assign):
            lines.extend(t.id for t in node.targets if isinstance(t, ast.Name) and t.id.isupper())
    return lines


def main(paths: list[str]) -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    for path in map(Path, paths):
        if path.suffix != ".py":
            continue
        try:
            lines = surface(ast.parse(path.read_text(encoding="utf-8"), filename=str(path)))
        except SyntaxError as exc:
            print(f"# {path}: could not parse ({exc.msg}, line {exc.lineno})\n")
            continue
        if lines:
            print(f"# {path}")
            print("\n".join(lines) + "\n")


if __name__ == "__main__":
    main(sys.argv[1:])
