import json

from .base_tool import BaseTool


class CalculatorTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="calculator",
            description="Performs basic mathematical operations such as addition, multiplication, subtraction, division, exponentiation, and modulus. Each operation must be called separately with structured JSON input.",
        )

    def multiply(self, a: float, b: float) -> float:
        return a * b

    def add(self, a: float, b: float) -> float:
        return a + b

    def subtract(self, a: float, b: float) -> float:
        return a - b

    def divide(self, a: float, b: float) -> float:
        if b == 0:
            return "Error: Division by zero is not allowed."
        return a / b

    def power(self, a: float, b: float) -> float:
        """Raises 'a' to the power of 'b'."""
        return a**b

    def modulus(self, a: float, b: float) -> float:
        result = int(a) % int(b)  # Ensure integer division before modulus
        return result

    def run(self, query: str) -> str:
        """
        Parses a structured JSON query and executes the corresponding mathematical function.

        Expected query format:
        {
            "operation": "add",
            "params": {"a": 5, "b": 3}
        }

        Returns the result as a string.
        """
        try:
            # Ensure query is valid JSON
            data = json.loads(query)

            # Validate JSON structure
            if "operation" not in data or "params" not in data:
                return "Error: Missing 'operation' or 'params' in request. Ensure the format is {'operation': 'add', 'params': {'a': 5, 'b': 3}}."

            operation = data["operation"]
            params = data["params"]

            if not isinstance(params, dict) or "a" not in params or "b" not in params:
                return "Error: Parameters must be in the format {'a': <num>, 'b': <num>}."

            if hasattr(self, operation):
                method = getattr(self, operation)
                return str(method(**params))
            else:
                return f"Error: Unknown operation '{operation}'. Available operations: add, multiply, subtract, divide, power, modulus."

        except json.JSONDecodeError:
            return "Error: Invalid JSON input. Ensure the input follows the format {'operation': 'add', 'params': {'a': 5, 'b': 3}}."
        except Exception as e:
            return f"Error: {str(e)}"


# === For standalone testing ===
if __name__ == "__main__":
    calculator_tool = CalculatorTool()

    test_queries = [
        '{"operation": "multiply", "params": {"a": 2, "b": 4}}',
        '{"operation": "add", "params": {"a": 10, "b": 5}}',
        '{"operation": "subtract", "params": {"a": 7, "b": 20}}',
        '{"operation": "divide", "params": {"a": 100, "b": 5}}',
        '{"operation": "power", "params": {"base": 2, "exponent": 3}}',
        '{"operation": "modulus", "params": {"a": 10, "b": 3}}',
    ]

    for query in test_queries:
        result = calculator_tool.run(query)
        print(f"Query: {query}\nResult: {result}\n")
