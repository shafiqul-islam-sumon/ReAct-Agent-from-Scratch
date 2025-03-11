import streamlit as st

from agent import ReActAgent


class WebApp:
    def __init__(self):
        self.agent = ReActAgent()
        self.initialize_ui()

    def initialize_ui(self):
        """Initializes the Streamlit UI components."""
        st.markdown(
            """
        <style>
            /* Remove default chat background */
            [data-testid="stChatMessage"] {
                background-color: transparent !important;
            }

            /* Chat message container (Flexbox layout for icon and text) */
            .chat-message-container {
                display: flex;
                align-items: center;
                gap: 12px;
                margin-bottom: 10px;
                width: 100%;
                max-width: 700px; /* Adjust as needed */
            }

            /* Chat message text box with background */
            .chat-message {
                padding: 12px;
                border-radius: 10px;
                width: fit-content;
                max-width: 85%;
            }

            /* User message style */
            .user-message {
                background-color: #D6EAF8;
            }

            /* Assistant message style */
            .assistant-message {
                background-color: #D5F5E3;
            }

            /* Larger Icon Styling */
            .message-icon {
                font-size: 32px; /* Increased size */
                min-width: 40px; /* Ensures spacing is even */
            }

            /* Text inside the message */
            .message-text {
                flex-grow: 1;
            }
        </style>
        """,
            unsafe_allow_html=True,
        )

        # st.title("ReAct Agent Chat")
        st.markdown(
            "<h1 style='text-align: center;'>ReAct Agent Chat</h1>",
            unsafe_allow_html=True,
        )

        with st.sidebar:
            st.title("Agent Chain of Thought")

        # Initialize chat history in session state
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []

        self.display_chat_history()
        self.handle_user_input()

    def display_chat_history(self):
        """Displays the chat history in the main chat."""
        for message in st.session_state.chat_history:
            self.display_message(message["role"], message["content"])

    def display_message(self, role, content):
        """Displays a chat message where only the text has a background color, keeping the icon outside."""
        if role == "user":
            icon = "👩‍💼"
            message_class = "user-message"
        else:
            icon = "🤖"
            message_class = "assistant-message"

        styled_content = f"""
        <div class="chat-message-container">
            <span class="message-icon">{icon}</span>
            <div class="chat-message {message_class}">
                <span class="message-text">{content}</span>
            </div>
        </div>
        """
        st.markdown(styled_content, unsafe_allow_html=True)

    def process_messages(self, messages):
        """Processes messages, classifying them into sidebar or main chat."""
        sidebar_messages = []
        main_messages = []
        final_answer = None

        for message in messages:
            role = message["role"]
            content = message["content"]

            # Extract final answer if present
            if "Final Answer:" in content:
                final_answer = content.split("Final Answer:", 1)[-1].strip()
                # content = content[:content.find("Final Answer:")].strip()

            # Sidebar messages (Chain of Thought)

            if "Thought:" in content or "Action:" in content or "PAUSE" in content or "Observation:" in content or "Final Answer:" in content:
                formatted_content = content.replace("Thought:", "\n:green[**Thought**]:").replace("Action:", "\n:blue[**Action**]:").replace("PAUSE", "\n:orange[**PAUSE**]").replace("Observation:", "\n:violet[**Observation**]:").replace("Final Answer:", "\n:red[**Final Answer**]:")
                sidebar_messages.append(formatted_content)
            elif content:
                main_messages.append({"role": role, "content": content})

        # Check if final answer is present and no main messages are present
        if final_answer and not main_messages:
            main_messages.append({"role": "assistant", "content": final_answer})

        return sidebar_messages, main_messages

    def handle_user_input(self):
        """Handles user input and processes responses."""
        if user_input := st.chat_input("How can I help?"):
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            self.display_message("user", user_input)

            # Get response from the agent
            try:
                result_messages = self.agent.execute(user_input)
                response_data = [{"role": msg.role, "content": msg.content} for msg in result_messages]

                # Process messages into sidebar and main chat
                sidebar_messages, main_messages = self.process_messages(response_data)

                # Display sidebar messages
                with st.sidebar:
                    for sidebar_msg in sidebar_messages:
                        st.markdown(sidebar_msg)

                # Display main chat messages
                for msg in main_messages:
                    st.session_state.chat_history.append(msg)
                    self.display_message(msg["role"], msg["content"])

            except Exception as e:
                st.error(f"An error occurred: {e}")


# Run the app
if __name__ == "__main__":
    WebApp()
