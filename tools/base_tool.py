from abc import ABC, abstractmethod


class BaseTool(ABC):
    """Abstract base class for all tools."""

    def __init__(self, name: str, description: str):
        """
        Initializes a tool with a name and description.

        :param name: Name of the tool (converted to lowercase for consistency).
        :param description: A brief description of the tool.
        """
        if not isinstance(name, str):
            raise ValueError("Tool name must be a string.")

        self._name = name.lower()  # Ensuring consistent lowercase tool names
        self._description = description

    @property
    def name(self) -> str:
        """Returns the tool's name."""
        return self._name

    @property
    def description(self) -> str:
        """Returns the tool's description."""
        return self._description

    @abstractmethod
    def run(self, query: str) -> str:
        """
        Abstract method that must be implemented by all tools.

        :param query: The input query for the tool.
        :return: The tool's response as a string.
        """
        pass
