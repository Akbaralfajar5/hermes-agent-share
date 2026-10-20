# X/Twitter Video Content Explanation Workflow

When user shares an X/Twitter video link and asks you to watch/explain it — you can't play embedded videos. Use this multi-source research approach.

## Trigger
User sends X/Twitter link with video, asks for explanation or summary. Often says "tolong tonton dan jelaskan" or similar.

## Workflow

### Step 1: Extract tweet text
Use fxtwitter to read the tweet metadata and text:
```
browser_navigate → https://fxtwitter.com/<user>/status/<id>
```
The page loads without auth. Use `browser_snapshot(full=true)` to read the article content. Extract:
- Tweet text (often describes the video topic)
- Video duration (shown as "MM:SS")
- Source attribution ("From <name>")
- Engagement metrics (indicates content quality/virality)

### Step 2: Identify the topic
From the tweet text, identify:
- **Person/speaker** mentioned (e.g., "founder of X", "Kirill")
- **Company/brand** mentioned (e.g., "Chinese AI company")
- **Subject matter** keywords (e.g., "agent swarms", "AI systems")
- **Scale/significance** markers (e.g., "$20B", "40 min masterclass")

### Step 3: Google search for context
Search for the topic using extracted keywords. Prioritize:
1. **Google AI Overview** — appears at top of search results, gives instant context
2. **Related X/Twitter threads** — often someone has written a thread breakdown
3. **Articles/blog posts** — Medium, Substack, company blogs
4. **YouTube videos** — often someone has made a summary video with timestamps

Search patterns:
```
"<person>" <company> <topic> <scale>
"<topic>" complete guide breakdown
site:x.com <username> "<topic>"
```

### Step 4: Cross-reference sources
Read 2-3 sources to build complete understanding:
- Google AI Overview for factual baseline
- Thread/article for detailed breakdown
- YouTube video descriptions for key points and timestamps

### Step 5: Synthesize and explain
Combine all sources into a coherent explanation in user's language. Structure:
1. **Siapa** — who is the speaker/company
2. **Apa** — what is the topic about
3. **Bagaimana** — how does it work (simplified)
4. **Kenapa penting** — why does it matter
5. **Fakta teknis** — key numbers/specs if relevant

## Pitfalls
- **xcancel.com and nitter.net** are unreliable — often blocked or show verification walls
- **fxtwitter.com redirects to x.com** on some browsers but the page title still contains tweet text
- **Google search with too-specific terms** returns no results — use broader topic keywords first
- **Don't claim to have watched the video** — be transparent that you researched the topic from multiple sources
- **User language matters** — if user asks in Indonesian, explain in Indonesian regardless of source language

## Example (real session)
User shared: `https://x.com/xiathis/status/2061475015250317812/video/1`

1. fxtwitter → tweet text in Spanish: "40 min masterclass from founder of Chinese AI company valued at $20B about agent swarms"
2. Google search "Kirill Chinese AI company $20B agent swarms" → Google AI Overview identified Moonshot AI, Kimi chatbot
3. Found related thread: "Kimi Agent Swarm: Complete A–Z Guide to How China Quietly Built a 300-Agent Parallel System"
4. Found YouTube video: "Claude Agent Teams VS Kimi Agent Swarm Explained" with key moments
5. Found company site: kimik2ai.com with technical specs
6. Synthesized into Indonesian explanation with analogies and technical details
