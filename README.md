# FastAPI Backend

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
```

2. Activate the virtual environment:
- On Windows: `venv\Scripts\activate`
- On macOS/Linux: `source venv/bin/activate`

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
Create `backend/.env` file with:

```env
SUPABASE_URL=https://owpvruoxqabwrazsabrg.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im93cHZydW94cWFid3JhenNhYnJnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjE1NjYwODUsImV4cCI6MjA3NzE0MjA4NX0.WK4o4hhBAnXqhypSxkA6x3goVL84skUVrm2ggN9H5e4
GEMINI_API_KEY=your_gemini_api_key_here
```

**Get your Gemini API key**: https://makersuite.google.com/app/apikey

5. Run the server:
```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

## Endpoints

- `GET /` - Health check
- `POST /analyze_transcript` - Analyze a transcript and provide insights
- `POST /generate_icebreaker` - Generate LinkedIn icebreakers
- `GET /feed` - Get all transcripts and icebreakers for the feed

## Environment Variables

Required variables in `.env`:
- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_KEY` - Your Supabase service role key
- `GEMINI_API_KEY` - Your Google Gemini API key (get from [Google AI Studio](https://makersuite.google.com/app/apikey))

## AI Integration

This backend uses **Google's Gemini Pro** for AI analysis:
- Free tier with generous rate limits
- No credit card required
- Text generation and analysis capabilities

See `../GEMINI_SETUP.md` for detailed AI setup instructions.

## CORS

The API is configured to allow requests from `http://localhost:3000` (Next.js dev server). Adjust the `allow_origins` in `main.py` if needed.
