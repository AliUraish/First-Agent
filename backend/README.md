# Email Flag Agent Backend

## Setup Instructions

1. Create a Google Cloud Project:
   - Go to [Google Cloud Console](https://console.cloud.google.com)
   - Create a new project or select an existing one
   - Enable the Gmail API for your project

2. Configure OAuth 2.0:
   - Go to APIs & Services > Credentials
   - Click "Create Credentials" > "OAuth client ID"
   - Select "Web application"
   - Add authorized redirect URI: `http://localhost:8000/auth/callback`
   - Download the client configuration file
   - Rename it to `credentials.json` and place it in the backend directory

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the server:
   ```bash
   uvicorn main:app --reload
   ```

## Environment Variables

Create a `details.env` file in the backend directory with the following content:
```env
DATABASE_URL=sqlite:///./app.db
```

## Security Notes

- Never commit `credentials.json` or `details.env` to version control
- Add both files to `.gitignore`
- Keep your OAuth client ID and secret secure 