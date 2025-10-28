from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import create_client, Client
import os
from dotenv import load_dotenv
import json
from groq import Groq

load_dotenv()

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://127.0.0.1:3000",
        "https://*.vercel.app",  # Allow all Vercel deployments
        "https://vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Supabase URL and KEY must be set in environment variables")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Groq AI Setup
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
groq_client = None
if GROQ_API_KEY:
    groq_client = Groq(api_key=GROQ_API_KEY)


# Pydantic models
class TranscriptRequest(BaseModel):
    transcript: str
    company_name: str = ""
    attendees: str = ""
    date: str = ""


class IcebreakerRequest(BaseModel):
    username: str
    role: str
    linkedin_bio: str
    deck_url: str = ""


# AI Helper function using Groq
async def call_ai(prompt: str) -> dict:
    """
    Call Groq AI to generate response.
    """
    if not GROQ_API_KEY or not groq_client:
        return {
            "summary": "Error: GROQ_API_KEY not configured. Please set your Groq API key in the .env file.",
            "insights": ["AI configuration needed"],
            "status": "error"
        }
    
    try:
        # Call Groq API using llama model
        response = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model="llama-3.1-8b-instant",  # Current Groq model
            temperature=0.7,
            max_tokens=1000
        )
        
        # Extract text from response
        ai_text = response.choices[0].message.content
        
        # Parse the response and structure it
        result = {
            "summary": ai_text,
            "insights": [],
            "status": "success"
        }
        
        return result
        
    except Exception as e:
        return {
            "summary": f"Error calling Groq API: {str(e)}",
            "insights": [],
            "status": "error"
        }


@app.get("/")
async def health():
    return {"status": "ok"}


@app.post("/analyze_transcript")
async def analyze_transcript(data: TranscriptRequest):
    """
    Analyze a transcript and provide insights.
    """
    try:
        # Create prompt
        prompt = f"""
        Review this transcript for {data.company_name}.
        Attendees: {data.attendees}
        Date: {data.date}

        Transcript:
        {data.transcript}

        Share:
        1. What I did well (and why)
        2. What I could do better next time
        3. Recommendations for improvement
        """

        # Call AI
        ai_response = await call_ai(prompt)

        # Save to Supabase
        result = supabase.table("transcripts").insert({
            "company_name": data.company_name,
            "attendees": data.attendees,
            "date": data.date,
            "transcript": data.transcript,
            "analysis": ai_response
        }).execute()

        return {"result": ai_response, "id": result.data[0]["id"] if result.data else None}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate_icebreaker")
async def generate_icebreaker(data: IcebreakerRequest):
    """
    Generate LinkedIn icebreaker based on profile information and deck.
    """
    try:
        # Create enhanced prompt
        prompt = f"""
        You are a sales expert analyzing a LinkedIn prospect for personalized outreach. Here's the prospect information:

        **Prospect Name:** {data.username}
        **Current Role:** {data.role}
        
        **LinkedIn About Section:**
        {data.linkedin_bio}

        **Pitch Deck Context:** {data.deck_url if data.deck_url else "No pitch deck provided"}

        Based on this information, provide a comprehensive icebreaker analysis with the following sections:

        ## 1. BUYING SIGNALS
        - Identify 3-5 specific indicators that suggest {data.username} might be interested in purchasing solutions
        - Look for pain points, growth initiatives, technology mentions, or business challenges
        - Reference their role as {data.role} and how it relates to potential needs

        ## 2. DISCOVERY TRIGGERS
        - Find 3-4 conversation starters based on their background
        - Identify shared connections, interests, or experiences
        - Highlight recent achievements or career moves worth mentioning

        ## 3. SMART QUESTIONS
        - Create 4-5 thoughtful, role-specific questions for {data.role}
        - Questions should demonstrate industry knowledge and genuine interest
        - Avoid generic questions - make them specific to their situation

        ## 4. PERSONALIZED OUTREACH APPROACH
        - Suggest the best way to approach {data.username} based on their communication style
        - Recommend timing and channel preferences
        - Identify what value proposition would resonate most

        ## 5. REFLECTION QUESTIONS
        - What are the top 3 things {data.username} would likely care about most?
        - What's unclear about their current situation that needs discovery?
        - What potential objections might they have and how to address them?

        Make the analysis specific to {data.username} as a {data.role} and avoid generic advice.
        """

        # Call AI
        ai_response = await call_ai(prompt)

        # Save to Supabase with new fields
        result = supabase.table("icebreakers").insert({
            "username": data.username,
            "role": data.role,
            "linkedin_bio": data.linkedin_bio,
            "deck_url": data.deck_url,
            "analysis": ai_response
        }).execute()

        return {"result": ai_response, "id": result.data[0]["id"] if result.data else None}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/feed")
async def get_feed():
    """
    Get all transcripts and icebreakers for the feed.
    """
    try:
        # Get transcripts
        transcripts_data = supabase.table("transcripts").select("*").order("created_at", desc=True).limit(20).execute()
        
        # Get icebreakers
        icebreakers_data = supabase.table("icebreakers").select("*").order("created_at", desc=True).limit(20).execute()
        
        feed_items = []
        
        # Format transcripts
        for item in transcripts_data.data:
            feed_items.append({
                "id": item["id"],
                "type": "transcript",
                "title": item.get("company_name", "Unknown Company"),
                "description": item.get("attendees", ""),
                "date": item.get("date", ""),
                "analysis": item.get("analysis", {}),
                "created_at": item.get("created_at", "")
            })
        
        # Format icebreakers
        for item in icebreakers_data.data:
            username = item.get("username", "Unknown User")
            role = item.get("role", "Unknown Role")
            feed_items.append({
                "id": item["id"],
                "type": "icebreaker",
                "title": f"LinkedIn Icebreaker - {username}",
                "description": f"{role} • Sales Outreach Analysis",
                "analysis": item.get("analysis", {}),
                "created_at": item.get("created_at", "")
            })
        
        # Sort by created_at
        feed_items.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        return {"items": feed_items}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
