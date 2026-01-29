from runnables import addition_runnable, subtraction_runnable, multiplication_runnable, division_runnable
from runnables import json_builder_runnable, json_parser_runnable
from runnables import prompt_formatter_runnable
from messages import message, chat_history

def running_tests(testScope):
    match testScope:
        case "Add":
            addition_runnable.testing()
        case "Sub":
            subtraction_runnable.testing()
        case "Mul":
            multiplication_runnable.testing()
        case "Div":
            division_runnable.testing()
        case "JsonB":
            json_builder_runnable.testing()
        case "JsonP":
            json_parser_runnable.testing()
        case "Messages":
            return message.testing()
        case "ChatH":
            return chat_history.testing()
        case "PromptF":
            return prompt_formatter_runnable.testing()
        case "All":
            addition_runnable.testing()
            subtraction_runnable.testing()
            multiplication_runnable.testing()
            division_runnable.testing()
            json_builder_runnable.testing()
            json_parser_runnable.testing()
            message.testing()
            chat_history.testing()
            prompt_formatter_runnable.testing()

if __name__ == "__main__":
    running_tests("PromptF")