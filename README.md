
# 1. Mentor

Mentor is a AI-powered educational assistant that allows users to analyze text and ask follow-up questions based on the analysis. It is designed to help users gain insights from their text content and engage in meaningful conversations with an AI assistant.

## 1.1. AI Assistant

The AI Assistant is the core component of the Mentor application. We use the Together AI platform as our cloud provider for AI models. Together AI offers a range of free large language models, which facilitates low-cost development of AI-powered applications without the need for local model deployment.

We decided to use the model `Llama-3.3-70B-Instruct-Turbo-Free` for being among the most powerful free models available on Together AI. It is capable of handling reasonably complex conversations, as well as maintaining contextual understanding across multiple interactions.

However, if desired, the user/developer can change the assistant underlying model and model provider platform by extending the `Assistant` class and updating the model-related environment variables (see `.env.example` for details). The Mentor application is designed to be flexible and can be adapted to use other models or providers in the future. The AI Assistant is implemented as an abstract class, allowing for easy extension and customization.

To implement a new AI Assistant, you can create a subclass of the `mentor.assistant.agent.Assistant` class and implement the `model` property to return the specific model instance you want to use. This allows for plug-and-play functionality, enabling the application to switch between different AI models or providers as needed.

For convenience, the `agent` module already provides `Assistant` interfaces for OpenAI, Azure OpenAI, and AWS Bedrock, which can be implemented in the future if desired. The current implementation uses the Together AI platform, but the architecture is designed to be flexible enough to accommodate other providers.

# 2. Tech Stack

- **Django** for the backend
- **PostgreSQL** for the database
- **Celery** for background tasks
- **Redis** for caching
- **Together AI** for AI-powered text analysis
- **LangChain** for language model interactions
- **DRF Spectacular** for API documentation and swagger UI
- **Docker Compose** for container orchestration
- **Poetry** for dependency management
- **MyPy** for static type checking
- **Ruff** for code formatting and linting
- **Pytest** for testing
- **Tox** for testing and linting automation

# 3. Running Mentor

## 3.1. Requirements

1. Docker Compose
1. A [Together AI](https://www.together.ai/) account

## 3.2. Installation and Execution

1. Clone the repository:
   ```bash
   git clone git@github.com:carolrizzi/mentor.git
   cd mentor
   ```

1. Create a file `deploy/.env` and add a variable `API_KEY` containing your Together AI API key. Alternatively, you can export the variable in your terminal session. Most environment variables have default values, but you can override them in the `.env` file or by exporting them in your terminal session. The `.env.example` file contains all the available environment variables and their default values.

1. Run docker compose:
   ```bash
   cd deploy
   docker compose up -d
   ```
   If you are running it for the first time, it might take some time to initialize the database after all containers are up and running. You can check the logs of the `mentor_api` container to see when the database is ready and the api is up and running.

Once the composer is up and running, you can access the API throught the swagger UI at http://127.0.0.1:8000/api/schema/swagger-ui/#/. The API documentation will be available at http://127.0.0.1:8000/api/schema/redoc/.

## 3.3. Usage

With the project running, open the [Swagger UI](http://127.0.0.1:8000/api/schema/swagger-ui/#/).

You will need to create a user to access the API. You can do this by sending a POST request to the `/api/register/` endpoint. The email field is optional and is not effectively used in this project.

This will return a JWT token that you can use to authenticate your requests. You can set the access token in the "Authorize" button on the top right corner. Once you have logged in, you can start using the API to create text analyses and send follow-up questions.

Follow up questions are always linked to a specific text analysis, consequently all conversations start with a text analysis request. You can request a text analysis by sending a POST request to the `/api/analysis/` endpoint. The title is optional and, if not provided, one will be generated automatically by the language model based on the text content.

This request will return a `task_id` that you can use to check the status of background task created to process the text analysis. You can check the status of the text analysis by sending a GET request to the `/api/task/{task_id}/` endpoint. The response will contain the status of the task and, once completed, the generated analysis.

It will also return a `session_id` that you can use to send follow-up questions and query the details of that session. You can send a follow-up question by sending a POST request to the `/api/question/` endpoint with the corresponding session ID. The question will be processed based on the context of the previous messages exchanged in the same session ID.

Like the analysis requestion, this question request will also return a `task_id` that you can use to check the status of the background task created to process the question. You can check the status of the question by sending a GET request to the `/api/task/{task_id}/` endpoint. The response will contain the status of the task and, once completed, the generated answer.

You can list all the initiated text analysis conversations by sending a GET request to the `/api/analysis/` endpoint. This will return a list of all sessions, including their IDs, titles, and creation dates. You can retrieve the details of a specific session by sending a GET request to the `/api/analysis/{session_id}/` endpoint. This will return all messages exchanged in that session, including the initial text analysis and any follow-up questions and answers.

An entire session and all its messages can be deleted by sending a DELETE request to the `/api/analysis/{session_id}/` endpoint. This will remove all messages and the session itself from the database.

For a full API reference, please refer to the [API documentation](http://127.0.0.1:8000/api/schema/redoc/).

# 4. Development

For local development, you will require Python 3.13.3 or higher (or Pyenv Python 3.13.3 installed) and Poetry for dependency management. You can set up your development environment by following these steps:

To set up your development environment, run the following in the repository root to install the required dependencies:
```bash
poetry install
```

To test the project, you can run it either with Docker Compose or locally with Poetry. To run it locally, first run docker compose with just the PostgreSQL and Redis services:
```bash
docker compose up -d db redis
```

To run the Django server locally, you will need to copy your `deploy/.env` file to the root of the project and ensure it contains the `API_KEY` variable with your Together AI API key. 

Then, you can run the Django development server with:
```bash
poetry run python mentor/manage.py runserver
```

And the celery worker with:
```bash
poetry run celery -A mentor.core worker --loglevel=info
```

To run the integration tests, run:
```bash
poetry run tox
```

We have provided a few text analysis and follow-up question examples in the file `test_data.json`.

# 5. Next Steps

Here are some ideas for future improvements and features:

- Move prompt storage and management to the database
- Add admin management with access to prompt management endpoints
- Add language detection and adaptation of prompts to the detected language

