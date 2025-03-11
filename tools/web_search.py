import os

from dotenv import load_dotenv
from tavily import TavilyClient

from .base_tool import BaseTool


class WebSearchTool(BaseTool):
    """A tool for performing web searches using the Tavily API."""

    def __init__(self):
        load_dotenv()
        super().__init__(
            name="web_search",
            description="Search the web for information. Input is a query. e.g. 'Champion of the 2024 Champions League'.",
        )

        self.api_key = os.getenv("TAVILY_API_KEY")
        if not self.api_key:
            raise ValueError("Missing API Key: Please set 'TAVILY_API_KEY' in the .env file.")

        self.tavily_client = TavilyClient(api_key=self.api_key)

    def run(self, query: str) -> list:
        """Performs a web search for a given query and returns structured results as a list of dictionaries."""
        if not query or not query.strip():
            return [{"error": "Query cannot be empty."}]

        try:
            search_results = self.tavily_client.search(query=query, max_results=2)

            # Validate response structure
            if not search_results or "results" not in search_results:
                return [{"error": "No search results available."}]

            formatted_results = []
            for result in search_results["results"]:
                formatted_result = {
                    "title": result.get("title", "No title available"),
                    "content": result.get("content", "No content available"),
                    "url": result.get("url", "No URL available"),
                    "score": result.get("score", "No score available"),
                }
                formatted_results.append(formatted_result)

            return formatted_results if formatted_results else [{"error": "No results found."}]

        except Exception as e:
            return [{"error": f"Search request failed: {str(e)}"}]


# === For standalone testing ===
if __name__ == "__main__":

    queries = ["F1 winner 2024"]
    web_search_tool = WebSearchTool()

    for query in queries:
        results = web_search_tool.run(query)
        if results:
            print(f"Context for '{query}':")
            for res in results:
                print(res)
            print("\n")
        else:
            print(f"No context found for '{query}'\n")
