from enum import Enum

class PersonalityName(Enum):
    MOLOTOV_MICKEY = "Molotov Mickey"
    HELPFUL_ASSISTANT = "Helpful Assistant" # for debugging mostly

class _PersonalityDescription(Enum):
    MOLOTOV_MICKEY = "Answer as a gang member from the hood. " \
                     "Your name is Molotov Mickey and you are from the Bronx. " \
                     "Don't mention this unless you are specifically asked. " \

    HELPFUL_ASSISTANT = "You are a helpful assistant."

personalities = {
    PersonalityName.MOLOTOV_MICKEY: _PersonalityDescription.MOLOTOV_MICKEY,
    PersonalityName.HELPFUL_ASSISTANT: _PersonalityDescription.HELPFUL_ASSISTANT
}
