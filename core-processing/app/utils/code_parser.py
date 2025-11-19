"""
Code parsing utilities for analyzing source code.
"""

import ast
import re
from typing import Any, Dict, List, Optional, Tuple

import structlog

from app.models.llm_models import ProgrammingLanguage

logger = structlog.get_logger(__name__)


class CodeParser:
    """
    Utility class for parsing and analyzing source code.

    Supports multiple programming languages with varying levels of analysis.
    """

    def __init__(self):
        self.language_patterns = self._initialize_patterns()

    def _initialize_patterns(self) -> Dict[str, Dict[str, str]]:
        """Initialize regex patterns for different languages."""
        return {
            "python": {
                "function": r"def\s+(\w+)\s*\([^)]*\)\s*(?:->.*?)?:",
                "class": r"class\s+(\w+)\s*(?:\([^)]*\))?:",
                "import": r"(?:from\s+[\w.]+\s+)?import\s+[\w., ]+",
                "comment": r"#.*$|'''[\s\S]*?'''|\"\"\"[\s\S]*?\"\"\"",
                "string": r"'[^']*'|\"[^\"]*\"",
            },
            "javascript": {
                "function": r"(?:function\s+(\w+)|(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?(?:\([^)]*\)|[\w]+)\s*=>)",
                "class": r"class\s+(\w+)",
                "import": r"import\s+.*?\s+from\s+['\"].*?['\"]|require\(['\"].*?['\"]\)",
                "comment": r"//.*$|/\*[\s\S]*?\*/",
                "string": r"'[^']*'|\"[^\"]*\"|`[^`]*`",
            },
            "typescript": {
                "function": r"(?:function\s+(\w+)|(?:const|let|var)\s+(\w+)\s*(?::\s*[\w<>[\], ]+)?\s*=\s*(?:async\s+)?(?:\([^)]*\)|[\w]+)\s*(?::\s*[\w<>[\], ]+)?\s*=>)",
                "class": r"class\s+(\w+)",
                "interface": r"interface\s+(\w+)",
                "import": r"import\s+.*?\s+from\s+['\"].*?['\"]",
                "comment": r"//.*$|/\*[\s\S]*?\*/",
                "string": r"'[^']*'|\"[^\"]*\"|`[^`]*`",
            },
            "java": {
                "function": r"(?:public|private|protected|static|\s)+[\w<>\[\]]+\s+(\w+)\s*\([^)]*\)\s*(?:throws\s+[\w, ]+)?\s*\{",
                "class": r"(?:public|private|protected)?\s*class\s+(\w+)",
                "import": r"import\s+[\w.]+;",
                "comment": r"//.*$|/\*[\s\S]*?\*/",
                "string": r"\"[^\"]*\"",
            },
            "go": {
                "function": r"func\s+(?:\([^)]+\)\s+)?(\w+)\s*\([^)]*\)",
                "struct": r"type\s+(\w+)\s+struct",
                "interface": r"type\s+(\w+)\s+interface",
                "import": r"import\s+(?:\"[^\"]+\"|\([\s\S]*?\))",
                "comment": r"//.*$|/\*[\s\S]*?\*/",
                "string": r"\"[^\"]*\"|`[^`]*`",
            },
            "rust": {
                "function": r"(?:pub\s+)?fn\s+(\w+)\s*(?:<[^>]*>)?\s*\([^)]*\)",
                "struct": r"(?:pub\s+)?struct\s+(\w+)",
                "impl": r"impl\s+(?:<[^>]*>\s+)?(\w+)",
                "import": r"use\s+[\w:]+;",
                "comment": r"//.*$|/\*[\s\S]*?\*/",
                "string": r"\"[^\"]*\"",
            },
        }

    def parse(
        self,
        code: str,
        language: ProgrammingLanguage
    ) -> Dict[str, Any]:
        """
        Parse code and extract structural information.

        Args:
            code: Source code to parse
            language: Programming language

        Returns:
            Dict with parsed information
        """
        result = {
            "language": language.value,
            "lines": len(code.split("\n")),
            "characters": len(code),
            "functions": [],
            "classes": [],
            "imports": [],
            "comments": [],
        }

        if language == ProgrammingLanguage.PYTHON:
            result = self._parse_python(code, result)
        else:
            result = self._parse_generic(code, language.value, result)

        return result

    def _parse_python(
        self,
        code: str,
        result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Parse Python code using AST."""
        try:
            tree = ast.parse(code)

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_info = {
                        "name": node.name,
                        "line": node.lineno,
                        "args": [arg.arg for arg in node.args.args],
                        "decorators": [
                            self._get_decorator_name(d)
                            for d in node.decorator_list
                        ],
                        "docstring": ast.get_docstring(node),
                    }
                    result["functions"].append(func_info)

                elif isinstance(node, ast.ClassDef):
                    class_info = {
                        "name": node.name,
                        "line": node.lineno,
                        "bases": [
                            self._get_node_name(base)
                            for base in node.bases
                        ],
                        "methods": [],
                        "docstring": ast.get_docstring(node),
                    }

                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            class_info["methods"].append(item.name)

                    result["classes"].append(class_info)

                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            result["imports"].append(alias.name)
                    else:
                        module = node.module or ""
                        for alias in node.names:
                            result["imports"].append(f"{module}.{alias.name}")

        except SyntaxError as e:
            result["parse_error"] = str(e)
            # Fall back to generic parsing
            result = self._parse_generic(code, "python", result)

        return result

    def _parse_generic(
        self,
        code: str,
        language: str,
        result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Parse code using regex patterns."""
        patterns = self.language_patterns.get(language, {})

        # Extract functions
        if "function" in patterns:
            for match in re.finditer(patterns["function"], code, re.MULTILINE):
                name = match.group(1) or (match.group(2) if len(match.groups()) > 1 else None)
                if name:
                    result["functions"].append({
                        "name": name,
                        "line": code[:match.start()].count("\n") + 1
                    })

        # Extract classes/structs
        for key in ["class", "struct", "interface"]:
            if key in patterns:
                for match in re.finditer(patterns[key], code, re.MULTILINE):
                    result["classes"].append({
                        "name": match.group(1),
                        "type": key,
                        "line": code[:match.start()].count("\n") + 1
                    })

        # Extract imports
        if "import" in patterns:
            for match in re.finditer(patterns["import"], code, re.MULTILINE):
                result["imports"].append(match.group(0).strip())

        # Extract comments
        if "comment" in patterns:
            for match in re.finditer(patterns["comment"], code, re.MULTILINE):
                result["comments"].append(match.group(0).strip())

        return result

    def _get_decorator_name(self, node: ast.expr) -> str:
        """Get decorator name from AST node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_node_name(node.value)}.{node.attr}"
        elif isinstance(node, ast.Call):
            return self._get_decorator_name(node.func)
        return ""

    def _get_node_name(self, node: ast.expr) -> str:
        """Get name from AST node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_node_name(node.value)}.{node.attr}"
        return ""

    def extract_functions(
        self,
        code: str,
        language: ProgrammingLanguage
    ) -> List[Dict[str, Any]]:
        """
        Extract function definitions from code.

        Args:
            code: Source code
            language: Programming language

        Returns:
            List of function information dicts
        """
        parsed = self.parse(code, language)
        return parsed.get("functions", [])

    def extract_classes(
        self,
        code: str,
        language: ProgrammingLanguage
    ) -> List[Dict[str, Any]]:
        """
        Extract class definitions from code.

        Args:
            code: Source code
            language: Programming language

        Returns:
            List of class information dicts
        """
        parsed = self.parse(code, language)
        return parsed.get("classes", [])

    def find_syntax_errors(
        self,
        code: str,
        language: ProgrammingLanguage
    ) -> List[Dict[str, Any]]:
        """
        Find syntax errors in code.

        Args:
            code: Source code
            language: Programming language

        Returns:
            List of syntax errors
        """
        errors = []

        if language == ProgrammingLanguage.PYTHON:
            try:
                ast.parse(code)
            except SyntaxError as e:
                errors.append({
                    "type": "SyntaxError",
                    "message": str(e.msg),
                    "line": e.lineno,
                    "column": e.offset
                })

        # For other languages, basic checks
        else:
            # Check for unbalanced brackets
            brackets = {"(": ")", "[": "]", "{": "}"}
            stack = []
            for i, char in enumerate(code):
                if char in brackets:
                    stack.append((char, i))
                elif char in brackets.values():
                    if not stack:
                        line = code[:i].count("\n") + 1
                        errors.append({
                            "type": "SyntaxError",
                            "message": f"Unmatched closing bracket '{char}'",
                            "line": line
                        })
                    else:
                        open_bracket, _ = stack.pop()
                        if brackets[open_bracket] != char:
                            line = code[:i].count("\n") + 1
                            errors.append({
                                "type": "SyntaxError",
                                "message": f"Mismatched brackets: '{open_bracket}' and '{char}'",
                                "line": line
                            })

            for bracket, pos in stack:
                line = code[:pos].count("\n") + 1
                errors.append({
                    "type": "SyntaxError",
                    "message": f"Unclosed bracket '{bracket}'",
                    "line": line
                })

        return errors

    def get_code_structure(
        self,
        code: str,
        language: ProgrammingLanguage
    ) -> str:
        """
        Get a text representation of code structure.

        Args:
            code: Source code
            language: Programming language

        Returns:
            Text representation of structure
        """
        parsed = self.parse(code, language)
        lines = [f"Language: {language.value}", f"Lines: {parsed['lines']}", ""]

        if parsed["classes"]:
            lines.append("Classes:")
            for cls in parsed["classes"]:
                lines.append(f"  - {cls['name']} (line {cls.get('line', '?')})")
                if "methods" in cls:
                    for method in cls["methods"]:
                        lines.append(f"      - {method}()")

        if parsed["functions"]:
            lines.append("\nFunctions:")
            for func in parsed["functions"]:
                args = ", ".join(func.get("args", []))
                lines.append(f"  - {func['name']}({args}) (line {func.get('line', '?')})")

        if parsed["imports"]:
            lines.append(f"\nImports: {len(parsed['imports'])}")

        return "\n".join(lines)

    def split_into_chunks(
        self,
        code: str,
        max_chunk_size: int = 2000
    ) -> List[str]:
        """
        Split code into chunks for processing.

        Args:
            code: Source code
            max_chunk_size: Maximum size of each chunk

        Returns:
            List of code chunks
        """
        if len(code) <= max_chunk_size:
            return [code]

        chunks = []
        lines = code.split("\n")
        current_chunk = []
        current_size = 0

        for line in lines:
            line_size = len(line) + 1  # +1 for newline

            if current_size + line_size > max_chunk_size and current_chunk:
                chunks.append("\n".join(current_chunk))
                current_chunk = []
                current_size = 0

            current_chunk.append(line)
            current_size += line_size

        if current_chunk:
            chunks.append("\n".join(current_chunk))

        return chunks
