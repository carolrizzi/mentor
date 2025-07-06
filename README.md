
# Mentor

# Requirements

3. Docker
4. A Together AI account

# Installation

1. Clone the repository:
   ```bash
   git clone git@github.com:carolrizzi/mentor.git
   cd mentor
   ```

2. Update the `.env` file with your Together AI API key:
   ```bash
   cp .env.example .env
   ```
   Then edit the `.env` file to include your API key:
   ```bash
   TOGETHER_API_KEY=your_api_key_here
   ```

3. Run docker compose:
   ```bash
   cd deploy
   docker compose up -d
   ```

<!-- TODO: change the URL host accordingly after wrap-up. Docker host might be different. -->
Once the composer is up and running, you can access the API throught the swagger at http://127.0.0.1:8000/api/schema/swagger-ui/#/. The API documentation will be available at http://127.0.0.1:8000/api/schema/redoc/.

You will need to create a user to access the API. You can do this by sending a POST request to the `/api/register/` endpoint with the following JSON body:
```json
{
  "username": "your_username",
  "password": "your_password"
}
```

This will return a JWT token that you can use to authenticate your requests. If you are using the Swagger UI, you can set the access token in the "Authorize" button on the top right corner. Once you have logged in, you can start using the API to create text analyses and send follow-up questions.

