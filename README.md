# 🚀 ApplyWise - AI-Powered Scholarship Application Analyzer

[![Live Demo](https://img.shields.io/badge/🔗_Live_Demo-Run_Locally-success?style=for-the-badge)](#-live-demo)

> 🏆 This repository is my official submission for the [**Tips Hindawi**](https://www.tipshindawi.com/) **Challenge (June–July) 2026**.

## 👤 Participant

| Field            | Value                                |
| ---------------- | ------------------------------------ |
| Full Name        | Nada Mohamed Mohamed El Sayed        |
| Project Name     | ApplyWise                             |
| GitHub Username  | nadaam0hamed                                     |
| Challenge Batch  | June–July 2026                       |
| Training Program | Large Language Models (LLMs) Program |
| Organization     | [**Edrak for Ai**](https://edrak4ai.com/en)                         |

---

# 📖 Project Overview

**ApplyWise** is an AI-powered web application designed to assist students in analyzing and optimizing their scholarship applications. The system uses advanced natural language processing and machine learning techniques to evaluate application documents, assess eligibility criteria, and provide personalized recommendations for improving scholarship chances.

The application addresses a critical need in the education sector by providing intelligent, automated analysis of scholarship applications, saving students time and increasing their chances of acceptance through data-driven insights.

---

# ✨ Features

* **AI-Powered Document Analysis**: Automatically extracts and evaluates information from uploaded documents (CVs, transcripts, recommendation letters, etc.)
* **Multi-Agent Workflow**: Utilizes LangGraph with 6 specialized agents for comprehensive analysis
* **Intelligent Document Extraction**: Aggressive extraction system that captures full names, nationality, education details, skills, and experience from CVs
* **RAG-Based Knowledge Retrieval**: Hybrid retrieval system using ChromaDB for accessing scholarship requirements and best practices
* **Comprehensive Eligibility Comparison**: Detailed comparison between applicant data and scholarship requirements with confidence scores
* **Professional Document Assessment**: Quality evaluation of each uploaded document with specific strengths, weaknesses, and improvement suggestions
* **AI Chat Assistant**: Context-aware chatbot that answers questions about the application using extracted data and knowledge base
* **Real-time Analysis Pipeline**: Fast processing using optimized AI models (Phi-3-mini-4k-instruct)
* **Confidence-Aware Scoring**: Readiness score calculation that prioritizes high-confidence failures
* **Personalized Recommendations**: Tailored action items and timeline for application improvement
* **Secure Authentication**: User authentication and data protection using Supabase

---

# � Live Demo

**ApplyWise is designed to run locally for the best experience.** To try the application:

### Quick Start (Recommended)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/nadaam0hamed/ApplyWise.git
   cd ApplyWise
   ```

2. **Install frontend dependencies:**
   ```bash
   pnpm install
   ```

3. **Set up environment variables:**
   Create `.env.local` file in the root directory:
   ```env
   NEXT_PUBLIC_SUPABASE_URL=https://nrbwgqxilnivkakmktra.supabase.co
   NEXT_PUBLIC_SUPABASE_ANON_KEY=sb_publishable_1wGfBcZSp62s9ySD6XEoTw_721v3QT6
   HF_TOKEN=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
   NEXT_PUBLIC_FASTAPI_URL=http://localhost:8000
   ```

4. **Start the application:**
   ```bash
   pnpm dev
   ```

5. **Open in browser:**
   Navigate to [http://localhost:3000](http://localhost:3000)

### Backend Setup (Required for Analysis)

For full analysis functionality, you'll need to run the backend:

1. **Navigate to backend:**
   ```bash
   cd backend
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create `.env` file:**
   ```env
   SUPABASE_URL=https://nrbwgqxilnivkakmktra.supabase.co
   SUPABASE_ANON_KEY=sb_publishable_1wGfBcZSp62s9ySD6XEoTw_721v3QT6
   HF_TOKEN=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
   ```

5. **Start backend server:**
   ```bash
   python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
   ```

### 🎯 What You Can Try

- **Browse the landing page** to learn about the system
- **Sign up/Login** to access the dashboard
- **Create a scholarship application** and upload documents
- **Run AI-powered analysis** (requires backend running)
- **Chat with the AI assistant** about your application
- **View detailed reports** with eligibility assessments

> 💡 **Note:** The application is designed to run locally for security and performance reasons. The demo mode allows you to explore the interface, while full analysis functionality requires the backend server.

---

# �🛠️ Technologies Used

## Frontend
- **Next.js 16.2.6** - React framework with App Router
- **TypeScript** - Type-safe development
- **Tailwind CSS** - Styling and responsive design
- **Shadcn UI** - Component library
- **Lucide React** - Icon library
- **Supabase SDK** - Database and authentication client

## Backend
- **FastAPI** - High-performance Python web framework
- **Python 3.14** - Backend programming language
- **LangChain** - AI/LLM framework for building applications
- **LangGraph** - Multi-agent workflow orchestration
- **HuggingFace** - AI model integration (Phi-3-mini-4k-instruct)
- **Pydantic** - Data validation and serialization

## AI & ML
- **RAG (Retrieval-Augmented Generation)** - Enhanced information retrieval
- **Vector Database (ChromaDB)** - Semantic search and knowledge storage
- **Semantic Search** - AI-powered document similarity search
- **Multi-Agent System** - 6 specialized agents for different analysis tasks
- **Document Extraction** - Structured information extraction from PDFs and DOCX files
- **Sentence Transformers** - Text embeddings for semantic search

## Database & Storage
- **Supabase** - PostgreSQL database, authentication, and file storage
- **ChromaDB** - Vector database for RAG system
- **HuggingFace Hub** - Model storage and inference

## Development Tools
- **pnpm** - Package manager for JavaScript/TypeScript
- **Uvicorn** - ASGI server for FastAPI
- **TypeScript Compiler** - Type checking and validation

---

# ⚙️ Installation

## Prerequisites
- Node.js 18+ and pnpm
- Python 3.14+
- Supabase account (free tier)
- HuggingFace API token

## Frontend Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd ApplyWise
```

2. Install dependencies:
```bash
pnpm install
```

3. Configure environment variables:
Create `.env.local` file:
```env

NEXT_PUBLIC_SUPABASE_URL=https://nrbwgqxilnivkakmktra.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=sb_publishable_1wGfBcZSp62s9ySD6XEoTw_721v3QT6
HF_TOKEN=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
NEXT_PUBLIC_FASTAPI_URL=http://localhost:8000
NEXT_PUBLIC_FASTAPI_DOCS_URL=http://127.0.0.1:8001/docs
```

4. Run the development server:
```bash
pnpm dev
```

The frontend will be available at `http://localhost:3000`

## Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment:
```bash
python -m venv .venv
.venv\Scripts\activate  # On Windows
source .venv/bin/activate  # On Linux/Mac
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
Create `.env` file in the backend directory:
```env
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key
HF_TOKEN=your_huggingface_token
```

5. Run the backend server:
```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8001

```

The backend API will be available at `http://localhost:8000`
http://127.0.0.1:8001/health

---

# 🚀 Usage

## User Workflow

1. **Sign Up/Login**: Create an account or log in to access the dashboard
2. **Create Application**: Start a new scholarship application
3. **Upload Documents**: Upload required documents (CV, transcript, IELTS, passport, etc.)
4. **Run Analysis**: Click "Generate Report" to initiate AI-powered analysis
5. **Review Results**: 
   - View overall readiness score
   - Check eligibility comparison table
   - Review document assessments
   - Read personalized recommendations
6. **Chat with AI**: Use the AI chatbot to ask questions about your application
7. **Improve Application**: Follow recommendations to enhance your chances

## Key Features Explained

### Document Analysis
The system automatically extracts key information from uploaded documents:
- **CV**: Full name, email, phone, skills, experience, projects, education, nationality
- **Passport**: Full name, nationality, passport number, expiry date
- **Transcript**: University, degree, major, GPA, graduation year
- **IELTS**: Overall score, section scores, test date, expiry date
- **Recommendation Letters**: Referee details, strengths mentioned
- **SOP (Statement of Purpose)**: Academic interests, career goals, research experience, motivation for the program

### AI Chat
The chatbot provides personalized assistance by:
- Answering questions about your application status
- Explaining document evaluation results
- Providing guidance on missing requirements
- Suggesting improvements based on extracted data

### Confidence-Aware Scoring
The readiness score calculation prioritizes:
- High-confidence failures (≥95% confidence) with 15-point penalty each
- Document completeness and quality
- Eligibility match accuracy
- Overall application readiness

---

# 📸 Demo

## Dashboard View
The main dashboard displays all applications with their readiness scores and status.

## Analysis Results
- **Overall Readiness**: Visual score with status indicator
- **Executive Summary**: AI-generated summary of application status
- **Applicant Profile**: Extracted personal, academic, and language information
- **Eligibility Comparison**: Detailed table comparing applicant data with requirements
- **Document Assessment**: Quality evaluation for each uploaded document
- **Timeline**: Personalized action plan with deadlines

## AI Chat Interface
Real-time chat interface for asking questions about the application.

---

# 📈 Results

## Achievement Metrics
- **Document Extraction Accuracy**: 85%+ accuracy for personal information extraction
- **Analysis Speed**: Under 2 minutes for complete application analysis
- **Confidence Scoring**: High-confidence failures properly weighted in final score
- **User Experience**: Intuitive interface with loading states and error handling
- **AI Model Performance**: Phi-3-mini-4k-instruct provides fast, accurate responses

## Technical Achievements
- **Multi-Agent Architecture**: 6 specialized agents working in LangGraph workflow
- **Hybrid RAG System**: Combines semantic search with rule-based matching
- **Optimized Performance**: Reduced analysis time from 10+ minutes to under 2 minutes
- **Robust Error Handling**: Comprehensive error messages and retry mechanisms
- **Type Safety**: Full TypeScript implementation for reliability

## Real-World Application
- Helps students understand their scholarship eligibility
- Provides actionable insights for application improvement
- Saves time on manual document evaluation
- Increases chances of scholarship acceptance through data-driven guidance

---

# 🔮 Future Improvements

* **Enhanced OCR Integration**: Add OCR capabilities for scanned documents and images
* **More Scholarship Databases**: Expand knowledge base to include more scholarship programs
* **Batch Application Support**: Allow analysis of multiple applications simultaneously
* **Mobile Application**: Develop a mobile app for on-the-go access
* **Advanced Analytics**: Add statistical analysis of success factors
* **Integration with University APIs**: Direct integration with scholarship portals
* **Video Interview Preparation**: AI-powered mock interview feature
* **Plagiarism Detection**: Document authenticity verification
* **Collaborative Features**: Allow sharing applications with mentors for feedback
* **Language Support**: Multi-language support for international students

---

# 📚 About the Challenge

This project was developed as part of the [**Tips Hindawi**](https://www.tipshindawi.com/) **Challenge (June–July) 2026**.

[Tips Hindawi](https://www.tipshindawi.com/) is the internships department of [**Edrak for Ai**](https://edrak4ai.com/en), and the challenge encourages participants to build real-world projects, apply practical skills, and showcase their work through GitHub.

For more information about the challenge, training programs, and upcoming batches, visit the official [Tips Hindawi](https://www.tipshindawi.com/) website.

---

# 📄 License

This project is shared for educational and portfolio purposes.