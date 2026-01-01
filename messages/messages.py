from datetime import datetime, timezone, timedelta
import random, string, time, re

# Implementation similar to that of LangChain.

class BaseMessage():
    def __init__(self, message_text: str, params: dict= None) -> None:
        self.name = self.__class__.__name__
        self.message_text = message_text
        self.params = {} if not params else params
        self.message_timestamp = datetime.now(timezone.utc)
        self.id = self._generate_id()

    def _generate_id(self) -> str:
        symbols_list = string.digits + string.ascii_lowercase
        id = ''.join(random.choice(symbols_list) for _ in range(9))
        return f'msg_{self.message_timestamp}_{id}'
    
    def get_type(self) -> str:
        raise NotImplementedError(
            f"Method not implemented. The class {self.__class__.__name__} must itself implement the get_type() method."
        )
    
    def to_prompt_format(self) -> dict:
        raise NotImplementedError(
            f"Method not implemented. The class {self.__class__.__name__} must itself implement the to_prompt_format() method."
        )
    
    def to_json(self) -> dict:
        return {
            "id": self.id,
            "timestamp": self.message_timestamp,
            "type": self.type,
            "message_text": self.message_text
        } | self.params
    
    def from_json(self, json_data):
        if not isinstance(json_data, dict):
            raise ValueError("Expected a dictionary for json_data.")

        required_fields = ["type", "message_text", "id", "timestamp"]
        for field in required_fields:
            if field not in json_data:
                raise ValueError(f"Missing required field: {field}.")

        message_class = MESSAGE_TYPES.get(json_data["type"])
        if not message_class:
            raise ValueError(f"Unknown message type: {json_data['type']}.")

        message = message_class(json_data["message_text"], json_data.get("params", {}))
        message.id = json_data["id"]
        message.timestamp = json_data["timestamp"]

        return message
    
    def __str__(self) -> str:
        local_offset = timedelta(seconds=-time.altzone if time.localtime().tm_isdst else -time.timezone)
        local_timezone = timezone(local_offset)
        local_time = self.message_timestamp.astimezone(local_timezone)
        formated_timestamp = local_time.strftime("%Y-%m-%d %H:%M:%S")
        return f'[{formated_timestamp}] {self.get_type().capitalize()}: {self.message_text}'
    
class AIMessage(BaseMessage):
    def __init__(self, message_text: str, params: dict = None) -> None:
        super().__init__(message_text, params)
        self.tool_calls = [] if not params["tool_calls"] else params["tool_calls"]

    def get_type(self) -> str:
        return "ai"
    
    def to_prompt_format(self) -> dict:
        formatted = { "role": "assistant", "message_text": self.message_text }
        if len(self.tool_calls) > 0:
            formatted["tool_calls"] = self.tool_calls
        return formatted
    
    def has_tool_calls(self) -> bool:
        return self.tool_calls > 0
    
    def get_tool_call(self, index: int = 0) -> str:
        return self.tool_calls[index]
    
class HumanMessage(BaseMessage):
    def __init__(self, message_text: str, params: dict = None) -> None:
        super().__init__(message_text, params)

    def get_type(self) -> str:
        return "human"
    
    def to_prompt_format(self) -> dict:
        return { "role": "user", "message_text": self.message_text }

class SystemMessage(BaseMessage):
    def __init__(self, message_text: str, params: dict = None) -> None:
        super().__init__(message_text, params)

    def get_type(self) -> str:
        return "system"
    
    def to_prompt_format(self) -> dict:
        return { "role": "system", "message_text": self.message_text }
    
class ToolMessage(BaseMessage):
    def __init__(self, message_text: str, tool_call_id: str, params: dict = None) -> None:
        super().__init__(message_text, params)
        self.tool_call_id = tool_call_id

    def get_type(self) -> str:
        return "tool"
    
    def to_prompt_format(self) -> dict:
        return { "role": "tool", "message_text": self.message_text }


MESSAGE_TYPES = {
  'ai': AIMessage,
  'human': HumanMessage,
  'system': SystemMessage,
  'tool': ToolMessage
}

# Helper functions
def messages_to_prompt_format(messages):
    return [msg.to_prompt_format() for msg in messages]

def filter_messages_by_type(messages, msg_type):
    return [msg for msg in messages if msg.type == msg_type]

def get_last_messages(messages, n):
    return messages[-n:]

def merge_consecutive_messages(messages):
    if not messages:
        return []
    
    merged = [messages[0]]
    for i in range(1, len(messages)):
        current = messages[i]
        last = merged[-1]
        
        # Merge if same type and both are strings
        if (current.get_type() == last.get_type() and isinstance(current.message_text, str) and isinstance(last.message_text, str) and current.get_type != "tool"):
            merged_content = last.message_text + "\n" + current.message_text
            merged[-1] = type(last)(merged_content, {**last.params, "merged": True})
        else:
            merged.append(current)
    
    return merged


def testing():
    print('Testing Messages:\n')

    try:
        system_msg = SystemMessage("System message content.")
        human_msg = HumanMessage("Hello AI, how are you?")
        ai_msg = AIMessage("I'm good, thank you for asking!", {"tool_calls": ["run_analysis"]})
        tool_msg = ToolMessage("Analysis result", "tool_call_123")

        print("Test 1: Convert to promp format.")
        messages = [system_msg, human_msg, ai_msg, tool_msg]
        prompt_messages = messages_to_prompt_format(messages)
        print(prompt_messages, "\n")
        print("Test 1 passed.\n")

        print("Test 2: Merge sequential messages of the same type.")
        merged_messages = merge_consecutive_messages([human_msg, HumanMessage("How are you?")])
        for msg in merged_messages:
            print(msg)
        pattern = r"\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\]"
        assert bool(re.search(pattern, str(merged_messages[0]))), f"Message does not contain correct timestamp {merged_messages[0]}"
        print("Test 2 passed.\n")

        print("Test 3: Merge sequential messages of different types.")
        merged_messages = merge_consecutive_messages([system_msg, human_msg, HumanMessage("How was your time off?"), ai_msg])
        for msg in merged_messages:
            print(msg)
        print("Test 3 passed.\n")

    except AssertionError as e:
        print('Error: : ', e)
    except Exception as e:
        print('Unexpected error: : ', e)


# Example Usage
if __name__ == "__main__":
    testing()