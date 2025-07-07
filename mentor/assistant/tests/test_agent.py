import uuid

import pytest

from mentor.assistant import agent


class FakePrompt:
    def __or__(self, other):
        return "FAKE_CHAIN"


@pytest.fixture
def fake_model(mocker):
    mock_model = mocker.Mock()
    mock_model.invoke.return_value = mocker.Mock(content="LLM result")
    return mock_model


@pytest.fixture
def fake_assistant(fake_model, mocker):
    class FakeAssistant(agent.Assistant):
        @property
        def model(self):
            return fake_model

    return FakeAssistant()


def test_get_prompt_reads_file(mocker):
    mock_read = mocker.patch("mentor.assistant.agent.read_text_file")
    mock_read.return_value = "Fake prompt text"

    result = agent.get_prompt(agent.PromptName.TEXT_ANALYSIS, agent.PromptType.SYSTEM)

    mock_read.assert_called_once()
    assert result == "Fake prompt text"


def test_generate_title(fake_assistant, mocker):
    mocker.patch(
        "mentor.assistant.agent.get_prompt",
        side_effect=[
            "System prompt text",
            "Human prompt text ",
        ],
    )

    result = fake_assistant.generate_title("some text")

    fake_assistant.model.invoke.assert_called_once()
    messages = fake_assistant.model.invoke.call_args[0][0]
    assert isinstance(messages, list)
    assert messages[0][0] == "system"
    assert messages[1][0] == "human"
    assert "some text" in messages[1][1]

    assert result.content == "LLM result"


def test_chain_with_history_invoke(mocker):
    fake_chain = mocker.Mock()
    fake_chain.invoke.return_value = mocker.Mock(content="Chain Result")

    session_id = uuid.uuid4()
    question = "Tell me something"

    result = agent.chain_with_history_invoke(
        chain=fake_chain,
        session_id=session_id,
        question=question,
    )

    fake_chain.invoke.assert_called_once()
    args, kwargs = fake_chain.invoke.call_args

    assert isinstance(args[0], dict)
    assert args[0]["question"] == question
    assert kwargs["config"]["configurable"]["session_id"] == str(session_id)

    assert result.content == "Chain Result"


def test_analyze_text_calls_chain_invoke(fake_assistant, mocker):
    fake_chain = mocker.Mock()
    fake_chain.invoke.return_value = mocker.Mock(content="Analysis Result")

    mocker.patch(
        "mentor.assistant.agent.get_chain_with_history", return_value=fake_chain
    )
    mocker.patch("mentor.assistant.agent.get_prompt", return_value="Human prompt ")

    session_id = uuid.uuid4()
    text = "This is my text"

    result = fake_assistant.analyze_text(session_id=session_id, text=text)

    fake_chain.invoke.assert_called_once()
    assert result.content == "Analysis Result"


def test_follow_up_question_calls_chain_invoke(fake_assistant, mocker):
    fake_chain = mocker.Mock()
    fake_chain.invoke.return_value = mocker.Mock(content="Follow-up result")

    mocker.patch(
        "mentor.assistant.agent.get_chain_with_history", return_value=fake_chain
    )

    session_id = uuid.uuid4()
    question = "My follow-up question"

    result = fake_assistant.follow_up_question(session_id=session_id, question=question)

    fake_chain.invoke.assert_called_once()
    assert result.content == "Follow-up result"
