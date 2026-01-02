from typing import TypeVar, Mapping, Iterable, Type, Tuple
from .message import BaseMessage, SystemMessage, HumanMessage, AIMessage, ToolMessage

ParamsT = TypeVar("ParamsT", bound=Mapping)
MessageT = TypeVar("MessageT", AIMessage, SystemError, ToolMessage, HumanMessage)

class ChatHistory():
    def __init__(self, params: ParamsT | None = None) -> None:
        self.name = self.__class__.__name__
        self.messages = []
        self.params = params or {}
        self.max_chat_length = self.params.get("max_chat_length", 50)
        self.preserve_sys_msg = self.params.get("preserve_sys_message", True)

    def _reorg_chat_memory(self) -> None:
        sys_messages_list = [msg for msg in self.messages if isinstance(msg, SystemMessage)]
        contains_sys_msg = len(sys_messages_list) > 0
        n_msgs_to_keep = self.max_chat_length if not contains_sys_msg else self.max_chat_length - 1
        sys_message = sys_messages_list[0] if contains_sys_msg else None
        most_recent_messages = [msg for msg in self.messages if not isinstance(msg, SystemMessage)][-n_msgs_to_keep:]

        if contains_sys_msg:
            self.messages = [sys_message] + most_recent_messages
        else:
            self.messages = most_recent_messages

    def add_message(self, messages: MessageT | Iterable[MessageT]):
         # Case 1: Single message.
        if isinstance(messages, BaseMessage):
            self.messages.append(messages)
        # Case 2: Iterable of messages.
        elif isinstance(messages, Iterable):
            for msg in messages:
                if not isinstance(msg, BaseMessage):
                    raise TypeError("All items must extend BaseMessage.")
                self.messages.append(msg)
                print(msg)
        # Case 3: Invalid input.
        else:
            raise TypeError("Message must be a BaseMessage or an iterable of BaseMessage.")
        self._reorg_chat_memory()

    def get_messages_by_type(self, type: Type[MessageT] | Tuple[Type[MessageT], ...]) -> Iterable[BaseMessage]:
        return [x for x in self.messages if isinstance(x, type)]
    
def testing():
    try:
        system_msg = SystemMessage("System message content.")
        human_msg = HumanMessage("Hello AI, how are you?")
        ai_msg = AIMessage("I'm good, thank you for asking!", {"tool_calls": ["run_analysis"]})
        tool_msg = ToolMessage("Analysis result", "tool_call_123")

        chat_history = ChatHistory()
        chat_history.add_message([human_msg, ai_msg, system_msg, tool_msg])

    except Exception as e:
        print("Unexpected error: ", e)

if __name__ == "__main__":
    testing()