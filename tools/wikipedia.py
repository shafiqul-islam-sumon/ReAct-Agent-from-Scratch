import wikipediaapi

from .base_tool import BaseTool


class WikipediaTool(BaseTool):
    """A tool for fetching Wikipedia summaries."""

    def __init__(self, language="en", user_agent="ReAct Agent from Scratch"):
        super().__init__(
            name="wikipedia",
            description="Gets information from a Wikipedia entry. Specific Wikipedia input. e.g. 'Albert Einstein'.",
        )
        self.wiki_api = wikipediaapi.Wikipedia(user_agent=user_agent, language=language)

    def run(self, query: str) -> dict:
        """Fetches summary information from Wikipedia for a given topic."""
        if not query or not query.strip():
            return {"error": "Query cannot be empty."}

        try:
            page = self.wiki_api.page(query)

            if page.exists():
                return {"query": query, "title": page.title, "summary": page.summary}

            return {"error": f"No Wikipedia page found for '{query}'."}

        except Exception as e:
            return {"error": f"An error occurred while searching Wikipedia: {str(e)}"}


# === For standalone testing ===
if __name__ == "__main__":

    wikipedia_tool = WikipediaTool()
    queries = ["Julian Alvarez"]

    for query in queries:
        result = wikipedia_tool.run(query)
        if result:
            print(f"Result for '{query}':\n{result}\n")
        else:
            print(f"No result found for '{query}'\n")
