/**
 * Processing Service
 * API service for Core Processing (AI/LLM) module
 */

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8003/api/v1';

/**
 * Helper function to make API requests
 */
async function apiRequest(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`;

  const defaultHeaders = {
    'Content-Type': 'application/json',
  };

  // Add auth token if available
  const token = localStorage.getItem('auth_token');
  if (token) {
    defaultHeaders['Authorization'] = `Bearer ${token}`;
  }

  const config = {
    ...options,
    headers: {
      ...defaultHeaders,
      ...options.headers,
    },
  };

  try {
    const response = await fetch(url, config);
    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.message || data.error?.message || 'API request failed');
    }

    return data;
  } catch (error) {
    if (error.name === 'TypeError' && error.message === 'Failed to fetch') {
      throw new Error('Unable to connect to the server. Please check your connection.');
    }
    throw error;
  }
}

/**
 * Generate code using AI
 * @param {Object} params - Generation parameters
 * @param {string} params.language - Programming language
 * @param {string} params.taskType - Type of code to generate (function, class, module, test)
 * @param {string} params.prompt - Description of code to generate
 * @returns {Promise<Object>} Generated code and metadata
 */
export async function generateCode({ language, taskType, prompt }) {
  // For development/demo purposes, return mock data
  // In production, this would call the actual API

  // Simulated API call
  return new Promise((resolve) => {
    setTimeout(() => {
      const mockCode = getMockGeneratedCode(language, taskType, prompt);
      resolve({
        code: mockCode,
        language,
        taskType,
        tokensUsed: Math.floor(Math.random() * 500) + 100,
        generationTime: Math.random() * 2 + 0.5,
      });
    }, 1500);
  });

  // Production API call:
  // return apiRequest('/processing/generate', {
  //   method: 'POST',
  //   body: JSON.stringify({ language, taskType, prompt }),
  // });
}

/**
 * Debug code using AI analysis
 * @param {Object} params - Debug parameters
 * @param {string} params.code - Code to debug
 * @param {string} params.errorMessage - Error message
 * @param {string} params.stackTrace - Stack trace
 * @param {string} params.language - Programming language
 * @returns {Promise<Object>} Debug analysis and suggested fixes
 */
export async function debugCode({ code, errorMessage, stackTrace, language }) {
  // Simulated API call for demo
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        bugType: 'Runtime Error',
        severity: 'high',
        location: { line: 5, column: 10 },
        explanation: 'The code attempts to access an undefined variable or property. This typically occurs when a variable is used before being declared or when accessing a property on a null/undefined value.',
        fixes: [
          {
            description: 'Add null check before accessing the property',
            fixedCode: getMockFixedCode(language, code, 'null-check'),
            confidence: 0.95,
          },
          {
            description: 'Initialize the variable with a default value',
            fixedCode: getMockFixedCode(language, code, 'default-value'),
            confidence: 0.85,
          },
        ],
        relatedIssues: [
          'Consider adding type annotations to prevent similar errors',
          'Use optional chaining for safer property access',
        ],
      });
    }, 2000);
  });

  // Production API call:
  // return apiRequest('/processing/debug', {
  //   method: 'POST',
  //   body: JSON.stringify({ code, errorMessage, stackTrace, language }),
  // });
}

/**
 * Optimize code using AI
 * @param {Object} params - Optimization parameters
 * @param {string} params.code - Code to optimize
 * @param {string} params.language - Programming language
 * @param {string} params.optimizationType - Type of optimization
 * @returns {Promise<Object>} Optimized code and suggestions
 */
export async function optimizeCode({ code, language, optimizationType }) {
  // Simulated API call for demo
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        optimizedCode: getMockOptimizedCode(language, code, optimizationType),
        suggestions: [
          {
            title: 'Use list comprehension',
            description: 'Replace the for loop with a list comprehension for better performance and readability.',
            category: optimizationType,
            impact: 'high',
            lineNumbers: [3, 4, 5],
          },
          {
            title: 'Cache repeated calculations',
            description: 'Store the result of repeated calculations in a variable to avoid redundant computation.',
            category: 'performance',
            impact: 'medium',
            lineNumbers: [8, 12],
          },
          {
            title: 'Use built-in functions',
            description: 'Replace custom implementation with optimized built-in functions.',
            category: 'performance',
            impact: 'medium',
            lineNumbers: [15],
          },
        ],
        metrics: {
          performanceImprovement: '35%',
          linesReduced: 5,
          complexityReduction: '20%',
        },
      });
    }, 2000);
  });

  // Production API call:
  // return apiRequest('/processing/optimize', {
  //   method: 'POST',
  //   body: JSON.stringify({ code, language, optimizationType }),
  // });
}

/**
 * Evaluate code quality using AI
 * @param {Object} params - Evaluation parameters
 * @param {string} params.code - Code to evaluate
 * @param {string} params.language - Programming language
 * @returns {Promise<Object>} Quality scores and issues
 */
export async function evaluateCode({ code, language }) {
  // Simulated API call for demo
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        scores: {
          readability: Math.floor(Math.random() * 30) + 70,
          performance: Math.floor(Math.random() * 40) + 60,
          maintainability: Math.floor(Math.random() * 35) + 65,
          security: Math.floor(Math.random() * 30) + 70,
          testability: Math.floor(Math.random() * 40) + 60,
          documentation: Math.floor(Math.random() * 50) + 50,
        },
        issues: [
          {
            severity: 'medium',
            line: 12,
            message: 'Function is too long. Consider breaking it into smaller functions.',
            suggestion: 'Extract the validation logic into a separate function for better readability.',
          },
          {
            severity: 'low',
            line: 5,
            message: 'Variable name is not descriptive.',
            suggestion: 'Rename "x" to something more meaningful like "userInput" or "value".',
          },
          {
            severity: 'high',
            line: 23,
            message: 'Potential SQL injection vulnerability.',
            suggestion: 'Use parameterized queries instead of string concatenation.',
          },
          {
            severity: 'info',
            line: 1,
            message: 'Missing function documentation.',
            suggestion: 'Add a docstring describing the function purpose, parameters, and return value.',
          },
        ],
        improvements: [
          {
            category: 'Performance',
            suggestion: 'Consider using a more efficient data structure for the lookup operation.',
            impact: 'Reduces time complexity from O(n) to O(1)',
          },
          {
            category: 'Readability',
            suggestion: 'Add type hints to function parameters and return values.',
            impact: 'Improves code clarity and IDE support',
          },
          {
            category: 'Testing',
            suggestion: 'Add unit tests for edge cases like empty input and null values.',
            impact: 'Increases code reliability and confidence in changes',
          },
        ],
      });
    }, 2000);
  });

  // Production API call:
  // return apiRequest('/processing/evaluate', {
  //   method: 'POST',
  //   body: JSON.stringify({ code, language }),
  // });
}

/**
 * Get processing history
 * @param {string} type - Type of processing (generation, debug, optimization, evaluation)
 * @param {number} limit - Maximum number of items to return
 * @returns {Promise<Array>} Processing history items
 */
export async function getProcessingHistory(type = 'all', limit = 50) {
  return apiRequest(`/processing/history?type=${type}&limit=${limit}`);
}

/**
 * Delete a history item
 * @param {string} id - History item ID
 * @returns {Promise<Object>} Deletion confirmation
 */
export async function deleteHistoryItem(id) {
  return apiRequest(`/processing/history/${id}`, {
    method: 'DELETE',
  });
}

// Mock data generators for development/demo

function getMockGeneratedCode(language, taskType, prompt) {
  const templates = {
    python: {
      function: `def process_data(data: list) -> dict:
    """
    Process the input data and return results.

    Args:
        data: List of items to process

    Returns:
        Dictionary containing processed results
    """
    if not data:
        return {"status": "empty", "count": 0}

    results = {
        "status": "success",
        "count": len(data),
        "processed": [],
        "summary": {}
    }

    for item in data:
        processed_item = {
            "original": item,
            "transformed": str(item).upper(),
            "length": len(str(item))
        }
        results["processed"].append(processed_item)

    # Calculate summary statistics
    lengths = [p["length"] for p in results["processed"]]
    results["summary"] = {
        "total_items": len(lengths),
        "avg_length": sum(lengths) / len(lengths) if lengths else 0,
        "max_length": max(lengths) if lengths else 0,
        "min_length": min(lengths) if lengths else 0
    }

    return results`,
      class: `class DataProcessor:
    """
    A class for processing and analyzing data.
    """

    def __init__(self, name: str = "default"):
        self.name = name
        self._data = []
        self._processed = False

    def load_data(self, data: list) -> None:
        """Load data for processing."""
        self._data = data
        self._processed = False

    def process(self) -> dict:
        """Process the loaded data."""
        if not self._data:
            raise ValueError("No data loaded")

        results = []
        for item in self._data:
            results.append(self._transform(item))

        self._processed = True
        return {"name": self.name, "results": results}

    def _transform(self, item):
        """Transform a single item."""
        return {"value": item, "type": type(item).__name__}

    @property
    def is_processed(self) -> bool:
        """Check if data has been processed."""
        return self._processed`,
      test: `import pytest
from your_module import process_data

class TestProcessData:
    """Test suite for process_data function."""

    def test_empty_input(self):
        """Test with empty list."""
        result = process_data([])
        assert result["status"] == "empty"
        assert result["count"] == 0

    def test_single_item(self):
        """Test with single item."""
        result = process_data(["hello"])
        assert result["count"] == 1
        assert len(result["processed"]) == 1

    def test_multiple_items(self):
        """Test with multiple items."""
        data = ["a", "bb", "ccc"]
        result = process_data(data)
        assert result["count"] == 3
        assert result["summary"]["min_length"] == 1
        assert result["summary"]["max_length"] == 3

    def test_transformation(self):
        """Test that items are transformed correctly."""
        result = process_data(["test"])
        assert result["processed"][0]["transformed"] == "TEST"

    @pytest.mark.parametrize("input_data,expected_count", [
        ([], 0),
        (["a"], 1),
        (["a", "b", "c"], 3),
    ])
    def test_count_parametrized(self, input_data, expected_count):
        """Parametrized test for count."""
        result = process_data(input_data)
        assert result["count"] == expected_count`,
    },
    javascript: {
      function: `/**
 * Process the input data and return results.
 * @param {Array} data - List of items to process
 * @returns {Object} Dictionary containing processed results
 */
function processData(data) {
  if (!data || data.length === 0) {
    return { status: 'empty', count: 0 };
  }

  const results = {
    status: 'success',
    count: data.length,
    processed: [],
    summary: {}
  };

  data.forEach(item => {
    const processedItem = {
      original: item,
      transformed: String(item).toUpperCase(),
      length: String(item).length
    };
    results.processed.push(processedItem);
  });

  // Calculate summary statistics
  const lengths = results.processed.map(p => p.length);
  results.summary = {
    totalItems: lengths.length,
    avgLength: lengths.reduce((a, b) => a + b, 0) / lengths.length,
    maxLength: Math.max(...lengths),
    minLength: Math.min(...lengths)
  };

  return results;
}

module.exports = { processData };`,
    },
  };

  const langTemplates = templates[language] || templates.python;
  return langTemplates[taskType] || langTemplates.function;
}

function getMockFixedCode(language, originalCode, fixType) {
  // Return a slightly modified version of the original code as a "fix"
  if (fixType === 'null-check') {
    return `// Added null check
if (value !== null && value !== undefined) {
${originalCode.split('\n').map(line => '  ' + line).join('\n')}
}`;
  }
  return originalCode + '\n\n// Default value added';
}

function getMockOptimizedCode(language, originalCode, optimizationType) {
  // Return the original code with some optimization comments
  return `# Optimized for ${optimizationType}
# - Reduced time complexity
# - Improved memory usage
# - Enhanced readability

${originalCode}

# Additional optimizations applied`;
}

export default {
  generateCode,
  debugCode,
  optimizeCode,
  evaluateCode,
  getProcessingHistory,
  deleteHistoryItem,
};
