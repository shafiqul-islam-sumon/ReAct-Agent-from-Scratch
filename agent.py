import importlib
import json
import os
import pkgutil
import re
from datetime import datetime

import tiktoken
from colorama import Fore, Style, init
from dotenv import load_dotenv
from openai import AzureOpenAI

from tools.base_tool import BaseTool
from utils.message import Message


class ReActAgent:
    def __init__(self):
        load_dotenv()

        self.tools = {}
        self.messages = []
        self.max_iterations = 10
        self.current_iteration = 0
        self.old_chats_summary = ""
        self.messages_to_summarize = 3
        self.llm_max_tokens = 500
        self.max_messages_tokens = 1000
        self.model = os.getenv("MODEL_NAME")
        self.client = self.get_llm_client()
        self.system_prompt = self.load_prompt("prompts/system_prompt.txt")
        self.summary_prompt = self.load_prompt("prompts/summary_prompt.txt")
        self.tokenizer = tiktoken.encoding_for_model(self.model)

        # Register tools dynamically
        self.register_tools()

    def get_llm_client(self):
        llm_client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("OPENAI_API_VERSION"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        )
        return llm_client

    def register_tools(self):
        """Dynamically registers all available tools."""
        tool_modules = [name for _, name, _ in pkgutil.iter_modules(["tools"])]

        for module_name in tool_modules:
            try:
                module = importlib.import_module(f"tools.{module_name}")
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if isinstance(attr, type) and issubclass(attr, BaseTool) and attr is not BaseTool:
                        tool_instance = attr()
                        self.tools[tool_instance.name.lower()] = tool_instance
            except Exception as e:
                print(f"\n{Fore.RED}[ERROR] Failed to register tool {module_name}: {e}{Style.RESET_ALL}\n")

    def get_tools(self):
        """Returns a formatted string listing available tools."""
        return "\n".join([f"{tool.name}: {tool.description}" for tool in self.tools.values()])

    def num_tokens_from_messages(self, messages):
        """Return the number of tokens used by a list of messages"""
        value = "".join([msg["content"] for msg in messages])  # Extract content from chat messages
        encoded = self.tokenizer.encode(value)  # Tokenize the extracted text

        return len(encoded)

    def num_tokens_from_text(self, text):
        """Return the number of tokens used by the given text."""
        encoded = self.tokenizer.encode(text)

        return len(encoded)

    def load_prompt(self, path):
        """Returns a prompt from a file."""
        with open(path, "r") as file:
            return file.read() if file else ""

    def add_message(self, role, content):
        """Add a message to the messages list."""
        self.messages.append(Message(role=role, content=content))

    def think(self):
        """Think and decide based on the response from OpenAI."""
        self.current_iteration += 1

        if self.current_iteration > self.max_iterations:
            print(f"\n{Fore.YELLOW}Reached maximum iterations. Stopping.{Style.RESET_ALL}")
            self.add_message(
                "assistant",
                "I'm sorry, but I couldn't find a satisfactory answer within the allowed number of iterations.",
            )
            return

        current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        prompt = self.system_prompt.format(tools=self.get_tools(), date=current_date)

        response = self.get_llm_response(prompt)
        self.add_message("assistant", response)

        # Print each thought immediately
        self.format_output(response)

        # Continue processing actions
        self.determine_action(response)

    def determine_action(self, response):
        """Decide on the next action based on the response, without using regex."""

        if "Final Answer:" in response:
            return

        # Find "Action:" in the response
        action_start = response.find("Action:")

        if action_start == -1:
            print(f"{Fore.YELLOW}No action or final answer found in the response.{Style.RESET_ALL}")
            return

        # Extract the action line
        action_line = response[action_start:].split("\n")[0].strip()

        # Remove the "Action:" prefix
        action_parts = action_line.replace("Action:", "").strip().split(":", 1)

        if len(action_parts) < 2:
            print(f"{Fore.RED}Error: Action format is incorrect: {action_line}{Style.RESET_ALL}")
            return

        tool_name = action_parts[0].strip().lower()
        query = action_parts[1].strip()

        # Handle calculator JSON validation
        if tool_name == "calculator":
            try:
                json_data = json.loads(query)

                if "operation" not in json_data:
                    print(f"{Fore.RED}Error: Missing 'operation' in calculator JSON: {query}{Style.RESET_ALL}")
                    return

                query = json.dumps(json_data)

            except json.JSONDecodeError:
                print(f"{Fore.RED}Error: Invalid JSON input for calculator: {query}{Style.RESET_ALL}")
                return

        # Execute the extracted action
        self.execute_action(tool_name, query)

    def execute_action(self, tool_name, query):
        """Act on the response by calling the appropriate tool."""
        tool = self.tools.get(tool_name)

        if tool:
            result = tool.run(query)
            observation = f"Observation: {tool_name} tool output: {result}"

            self.add_message("system", observation)

            # Print the observation immediately
            print(f"{Fore.CYAN}\n[SYSTEM]:{Style.RESET_ALL} {observation}\n")

            # Continue thinking after receiving observation
            self.think()
        else:
            error_msg = f"Error: Tool '{tool_name}' not found"
            print(f"\n{Fore.RED}{error_msg}{Style.RESET_ALL}")
            self.add_message("system", error_msg)
            self.think()  # Continue processing other actions

    def format_output(self, response):
        """Format output for better readability."""
        response = re.sub(r"Final Answer:", f"{Fore.RED}\n[FINAL ANSWER]:{Style.RESET_ALL}", response)
        response = re.sub(r"Action:", f"{Fore.YELLOW}\n[ACTION]:{Style.RESET_ALL}", response)
        response = re.sub(r"PAUSE", f"{Fore.MAGENTA}\n[PAUSE]:{Style.RESET_ALL}", response)

        print(f"{Fore.GREEN}\n[ASSISTANT]:{Style.RESET_ALL} {response}\n")

    def get_llm_response(self, prompt):
        """Call the OpenAI API to get a response."""
        chat_history = [
            {
                "role": message.role,
                "content": message.content,
            }
            for message in self.messages
        ]

        self.memory_management(chat_history)

        if self.old_chats_summary:
            prompt += f"\n\nOld messages summary:\n{self.old_chats_summary}"

        messages = [{"role": "system", "content": prompt}] + chat_history

        raw_response = self.client.chat.completions.create(model=self.model, messages=messages, max_tokens=self.llm_max_tokens)
        response = raw_response.choices[0].message.content

        return response.strip() if response else "No response from LLM"

    def summarize_old_chats(self, chats):
        """Summarizes old chat history and returns a concise summary response."""
        prompt = self.summary_prompt.format(chats=chats)
        messages = [{"role": "system", "content": prompt}]

        raw_response = self.client.chat.completions.create(model=self.model, messages=messages, max_tokens=self.llm_max_tokens)
        response = raw_response.choices[0].message.content

        return response.strip() if response else "No response from LLM"

    def get_indices(self, chat_history):
        """Extracts a specified number of consecutive user queries from the given chat history."""
        user_indices = [i for i, msg in enumerate(chat_history) if msg["role"] == "user"]

        start_index = user_indices[0]
        end_index = user_indices[self.messages_to_summarize]

        return start_index, end_index

    def memory_management(self, chat_history):
        """Manages memory by summarizing and deleting old chat history"""
        try:
            user_messages = [msg for msg in chat_history if msg["role"] == "user"]
            if len(user_messages) > self.messages_to_summarize and self.num_tokens_from_messages(chat_history) > self.max_messages_tokens:
                indices = self.get_indices(chat_history)
                if indices:
                    start_index, end_index = indices
                    chats = chat_history[start_index:end_index]
                    new_summary = self.summarize_old_chats(chats)
                    print(f"##### Tokens used by the old messages: {self.num_tokens_from_messages(chats)}")
                    # print("##### New Summary : ", new_summary)
                    if new_summary != "No response from LLM":
                        print(f"##### Tokens used by the new summary: {self.num_tokens_from_text(new_summary)}")
                        self.old_chats_summary = f"{self.old_chats_summary} {new_summary}".strip()
                        print("##### Old messages summary : ", self.old_chats_summary)
                        del self.messages[start_index:end_index]
        except Exception as e:
            print(f"An error occurred during memory management: {e}")

    def execute(self, query):
        """Execute a user query and return the full Agent response."""
        self.current_iteration = 0
        self.add_message("user", query)
        self.think()

        result_messages = []
        for message in self.messages[::-1]:
            if message.role == "user":
                break
            elif message.role != "user":
                result_messages.append(message)

        return result_messages[::-1]


if __name__ == "__main__":
    init(autoreset=True)
    react_agent = ReActAgent()

    while True:
        query = input(f"{Fore.CYAN}USER:{Style.RESET_ALL} ").strip()
        if query.lower() in ["exit", "quit"]:
            print(f"{Fore.YELLOW}Exiting the ReAct agent. Goodbye!{Style.RESET_ALL}")
            break

        result = react_agent.execute(query)
        # print('#### Result : ', result)
        print("\n" + "=" * 60 + "\n")
