"""
LLM prompt templates for code generation tasks.
"""

from typing import Dict

from app.models.llm_models import ProgrammingLanguage, TaskType


class PromptTemplates:
    """
    Collection of prompt templates for different code generation tasks.
    """

    def __init__(self):
        self.generation_templates = self._initialize_generation_templates()
        self.debug_templates = self._initialize_debug_templates()
        self.optimization_templates = self._initialize_optimization_templates()

    def _initialize_generation_templates(self) -> Dict[str, Dict[str, str]]:
        """Initialize generation prompt templates."""
        return {
            ProgrammingLanguage.PYTHON.value: {
                TaskType.FUNCTION.value: """
Write a Python function that accomplishes the task.
Follow these guidelines:
- Use type hints for parameters and return values
- Include a docstring with description, args, and returns
- Handle edge cases appropriately
- Follow PEP 8 style guidelines

```python
""",
                TaskType.CLASS.value: """
Write a Python class that accomplishes the task.
Follow these guidelines:
- Use type hints for attributes and methods
- Include docstrings for class and methods
- Implement __init__, __repr__, and other dunder methods as needed
- Follow PEP 8 style guidelines

```python
""",
                TaskType.TEST.value: """
Write Python unit tests using pytest.
Follow these guidelines:
- Test normal cases, edge cases, and error cases
- Use descriptive test names
- Use fixtures where appropriate
- Include assertions with clear messages

```python
import pytest

""",
                TaskType.MODULE.value: """
Write a Python module that accomplishes the task.
Follow these guidelines:
- Organize code into functions and classes
- Include module-level docstring
- Define __all__ for public API
- Add appropriate imports

```python
""",
            },
            ProgrammingLanguage.JAVASCRIPT.value: {
                TaskType.FUNCTION.value: """
Write a JavaScript function that accomplishes the task.
Follow these guidelines:
- Use ES6+ syntax
- Add JSDoc comments
- Handle errors appropriately
- Use meaningful variable names

```javascript
""",
                TaskType.CLASS.value: """
Write a JavaScript class that accomplishes the task.
Follow these guidelines:
- Use ES6+ class syntax
- Add JSDoc comments
- Implement constructor and methods
- Use private fields where appropriate (#)

```javascript
""",
                TaskType.TEST.value: """
Write JavaScript tests using Jest.
Follow these guidelines:
- Test normal cases, edge cases, and error cases
- Use descriptive test names
- Use beforeEach/afterEach where appropriate

```javascript
describe('', () => {
""",
            },
            ProgrammingLanguage.TYPESCRIPT.value: {
                TaskType.FUNCTION.value: """
Write a TypeScript function that accomplishes the task.
Follow these guidelines:
- Use proper type annotations
- Define interfaces for complex types
- Handle errors with proper typing
- Add JSDoc comments

```typescript
""",
                TaskType.CLASS.value: """
Write a TypeScript class that accomplishes the task.
Follow these guidelines:
- Use proper type annotations
- Define interfaces for data structures
- Use access modifiers (public, private, protected)
- Implement proper encapsulation

```typescript
""",
            },
            ProgrammingLanguage.JAVA.value: {
                TaskType.FUNCTION.value: """
Write a Java method that accomplishes the task.
Follow these guidelines:
- Use appropriate access modifiers
- Add Javadoc comments
- Handle exceptions properly
- Follow Java naming conventions

```java
""",
                TaskType.CLASS.value: """
Write a Java class that accomplishes the task.
Follow these guidelines:
- Use appropriate access modifiers
- Add Javadoc comments
- Implement constructor, getters, setters
- Consider implementing equals, hashCode, toString

```java
""",
            },
            ProgrammingLanguage.GO.value: {
                TaskType.FUNCTION.value: """
Write a Go function that accomplishes the task.
Follow these guidelines:
- Use meaningful names following Go conventions
- Return errors instead of panicking
- Add comments for exported functions
- Use pointers appropriately

```go
""",
                TaskType.CLASS.value: """
Write a Go struct with methods that accomplishes the task.
Follow these guidelines:
- Define struct with proper field types
- Add methods with appropriate receivers
- Handle errors properly
- Follow Go idioms

```go
""",
            },
            ProgrammingLanguage.RUST.value: {
                TaskType.FUNCTION.value: """
Write a Rust function that accomplishes the task.
Follow these guidelines:
- Use proper ownership and borrowing
- Return Result for fallible operations
- Add documentation comments (///)
- Follow Rust idioms

```rust
""",
                TaskType.CLASS.value: """
Write a Rust struct with impl that accomplishes the task.
Follow these guidelines:
- Define struct with proper field types
- Implement methods in impl block
- Consider implementing common traits
- Handle errors with Result

```rust
""",
            },
        }

    def _initialize_debug_templates(self) -> Dict[str, str]:
        """Initialize debug prompt templates."""
        return {
            "analyze": """
Analyze the following code for bugs, errors, and issues:

{code}

Error (if any): {error}

Identify:
1. Root cause of the error
2. All bugs and issues
3. Potential improvements
""",
            "fix": """
Fix the following code:

{code}

Error: {error}

Provide:
1. Corrected code
2. Explanation of each fix
3. Prevention suggestions
""",
            "explain_error": """
Explain the following error in simple terms:

Error: {error}
Language: {language}

Provide:
1. What the error means
2. Common causes
3. How to fix it
4. How to prevent it
""",
        }

    def _initialize_optimization_templates(self) -> Dict[str, str]:
        """Initialize optimization prompt templates."""
        return {
            "performance": """
Optimize the following code for better performance:

{code}

Focus on:
- Time complexity improvements
- Memory usage optimization
- Algorithmic improvements
- Caching opportunities

Provide optimized code and explain the improvements.
""",
            "readability": """
Improve the readability of the following code:

{code}

Focus on:
- Clear variable and function names
- Proper code structure
- Comments and documentation
- Consistent style

Provide improved code and explain the changes.
""",
            "security": """
Review and improve the security of the following code:

{code}

Check for:
- Input validation
- SQL injection
- XSS vulnerabilities
- Authentication/authorization issues
- Sensitive data handling

Provide secured code and explain the improvements.
""",
            "refactor": """
Refactor the following code for better maintainability:

{code}

Apply:
- SOLID principles
- DRY principle
- Proper separation of concerns
- Design patterns where appropriate

Provide refactored code and explain the changes.
""",
        }

    def get_generation_template(
        self,
        language: ProgrammingLanguage,
        task_type: TaskType
    ) -> str:
        """
        Get generation template for language and task type.

        Args:
            language: Programming language
            task_type: Type of generation task

        Returns:
            Prompt template string
        """
        language_templates = self.generation_templates.get(
            language.value,
            self.generation_templates.get(ProgrammingLanguage.PYTHON.value, {})
        )

        return language_templates.get(
            task_type.value,
            language_templates.get(TaskType.FUNCTION.value, "Generate code:\n```")
        )

    def get_debug_template(self, template_name: str = "fix") -> str:
        """
        Get debug template by name.

        Args:
            template_name: Name of the template

        Returns:
            Prompt template string
        """
        return self.debug_templates.get(template_name, self.debug_templates["fix"])

    def get_optimization_template(self, goal: str = "performance") -> str:
        """
        Get optimization template by goal.

        Args:
            goal: Optimization goal

        Returns:
            Prompt template string
        """
        return self.optimization_templates.get(
            goal,
            self.optimization_templates["performance"]
        )

    def format_template(self, template: str, **kwargs) -> str:
        """
        Format a template with provided values.

        Args:
            template: Template string
            **kwargs: Values to substitute

        Returns:
            Formatted string
        """
        return template.format(**kwargs)

    def create_system_prompt(self, role: str = "developer") -> str:
        """
        Create a system prompt for the LLM.

        Args:
            role: Role description

        Returns:
            System prompt string
        """
        prompts = {
            "developer": """You are an expert software developer with deep knowledge of multiple programming languages and best practices. You write clean, efficient, and well-documented code. You follow industry standards and conventions for each language.""",

            "debugger": """You are an expert debugger and code analyst. You excel at finding bugs, understanding error messages, and providing clear fixes. You explain issues in a way that helps developers learn and prevent similar problems.""",

            "optimizer": """You are an expert in code optimization and performance tuning. You identify bottlenecks, suggest algorithmic improvements, and optimize for both time and space complexity while maintaining code readability.""",

            "reviewer": """You are an expert code reviewer. You evaluate code quality, identify issues, suggest improvements, and ensure adherence to best practices and coding standards.""",
        }

        return prompts.get(role, prompts["developer"])

    def get_few_shot_examples(
        self,
        language: ProgrammingLanguage,
        task_type: TaskType
    ) -> list:
        """
        Get few-shot examples for a task.

        Args:
            language: Programming language
            task_type: Type of task

        Returns:
            List of example dicts
        """
        if language == ProgrammingLanguage.PYTHON and task_type == TaskType.FUNCTION:
            return [
                {
                    "input": "Create a function to check if a number is prime",
                    "output": '''def is_prime(n: int) -> bool:
    """
    Check if a number is prime.

    Args:
        n: The number to check

    Returns:
        True if the number is prime, False otherwise
    """
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    for i in range(3, int(n ** 0.5) + 1, 2):
        if n % i == 0:
            return False
    return True'''
                },
                {
                    "input": "Create a function to reverse a string",
                    "output": '''def reverse_string(s: str) -> str:
    """
    Reverse a string.

    Args:
        s: The string to reverse

    Returns:
        The reversed string
    """
    return s[::-1]'''
                }
            ]

        return []
