# AI Post Genie - Social Media Content Generator

## Overview
AI Post Genie is a full-stack web application that helps users generate engaging social media content using AI. Built with Flask backend and vanilla JavaScript frontend, featuring user authentication, subscription management, and OpenAI integration.

## Current State
- ✅ **Backend**: Flask application with PostgreSQL database
- ✅ **Authentication**: Replit Auth integration for user login/signup
- ✅ **AI Integration**: OpenAI GPT-4o-mini for content generation
- ✅ **Payments**: Stripe integration for subscription management
- ✅ **Frontend**: Responsive Bootstrap-based UI
- ✅ **Database**: PostgreSQL with user, generation, and payment models
- ✅ **Deployment**: Ready for Replit deployment

## Features
1. **User Authentication**: Email-based signup/login via Replit Auth
2. **Content Generation**: AI-powered social media posts, hashtags, and schedules
3. **Subscription Tiers**: 
   - Free: 1 generation/day
   - Pro: $9/month for unlimited generations
4. **Payment Processing**: Stripe Checkout and webhook handling
5. **Responsive UI**: Mobile-friendly Bootstrap interface
6. **Usage Tracking**: Daily generation limits and subscription status

## Project Architecture
- **Backend**: Flask with SQLAlchemy ORM
- **Database**: PostgreSQL (via Replit integration)
- **Authentication**: Replit Auth with OAuth
- **AI Service**: OpenAI GPT-4o-mini API
- **Payments**: Stripe API with webhooks
- **Frontend**: Bootstrap 5, vanilla JavaScript

## Recent Changes (2025-09-29)
- Created complete Flask application structure
- Implemented user authentication with Replit Auth
- Added OpenAI integration for content generation
- Built Stripe subscription system with webhooks
- Created responsive frontend with Bootstrap
- Added comprehensive error handling and validation
- Configured database models for users, generations, and payments

## User Preferences
- Framework: Flask (Python backend)
- Frontend: Bootstrap with vanilla JavaScript
- Database: PostgreSQL
- Payment: Stripe
- Authentication: Replit Auth
- AI Provider: OpenAI

## Environment Variables Required
- `OPENAI_API_KEY`: For AI content generation
- `STRIPE_SECRET_KEY`: For payment processing
- `SESSION_SECRET`: For Flask session management (auto-provided)
- `DATABASE_URL`: PostgreSQL connection (auto-provided)

## Key Files
- `main.py`: Application entry point
- `app.py`: Flask application configuration
- `routes.py`: API endpoints and route handlers
- `models.py`: Database models
- `replit_auth.py`: Authentication middleware
- `openai_service.py`: AI content generation service
- `templates/`: HTML templates (landing, dashboard, FAQ)

## Testing Status
- ✅ Flask server running on port 5000
- ✅ Landing page loading correctly
- ✅ Authentication protection working
- ✅ Database models created
- ✅ API endpoints configured
- 🔄 End-to-end testing in progress

## Deployment
Application is configured for Replit deployment with:
- Workflow configured for automatic startup
- CORS enabled for cross-origin requests
- Proper host binding (0.0.0.0:5000)
- Cache control headers for development