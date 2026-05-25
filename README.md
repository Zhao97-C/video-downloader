# SaveAny - Video Downloader

A cross-platform video download web application powered by yt-dlp.

## Features

- Download videos from 1000+ platforms (YouTube, TikTok, Instagram, Twitter, Bilibili, etc.)
- Multiple quality options up to 4K
- Smart download mode (direct link / proxy / streaming)
- Subtitle / transcript viewer with timestamps (login)
- AI video summaries (PRO)
- Subtitle translation (PRO)
- Batch playlist downloads (PRO)
- Mobile-friendly responsive design

## Tech Stack

- **Frontend**: Vue 3 + Vite + Tailwind CSS
- **Backend**: FastAPI + yt-dlp
- **Database**: SQLite (dev) / PostgreSQL (prod)
- **Payment**: Stripe
- **AI**: OpenAI GPT-4o-mini

## Quick Start

### Prerequisites

- Node.js 20+
- Python 3.12+
- ffmpeg

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Backend

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env  # Edit with your keys
uvicorn app.main:app --reload
```

### Docker Deployment

```bash
docker-compose up -d
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | /api/parse | Parse video URL |
| GET | /api/download/{task_id} | Download video |
| POST | /api/auth/register | Register |
| POST | /api/auth/login | Login |
| GET | /api/auth/profile | User profile |
| POST | /api/payment/create-checkout | Create Stripe checkout |
| POST | /api/payment/webhook | Stripe webhook |
| POST | /api/ai/subtitles | Fetch subtitles/transcript (login) |
| POST | /api/ai/summarize | AI video summary (PRO) |
| POST | /api/ai/translate-subtitle | Subtitle translation (PRO, `task_id`) |

## License

MIT
