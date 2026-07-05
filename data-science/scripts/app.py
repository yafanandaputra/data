import os
import sys
import tempfile
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List

# Add current directory to path to ensure imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from analyzer_engine import CVAnalyzerEngine

app = FastAPI(
    title="CV AI Analyzer Service",
    description="NLP-based parsing and job matching service for resumes",
    version="1.0.0"
)

# Allow Next.js dev server + production Vercel domain to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://sistem-informasi-pemagangan-mahasis-eta.vercel.app",
    ],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = CVAnalyzerEngine()

class MatchRequest(BaseModel):
    cv_skills: List[str]
    cv_education: str
    job_title: str
    job_requirements: str

@app.post("/analyze")
async def analyze_cv(
    file: Optional[UploadFile] = File(None),
    text: Optional[str] = Form(None)
):
    """Parses a resume (from file or raw text) and extracts name, contact info, education level, and skills."""
    if not file and not text:
        raise HTTPException(status_code=400, detail="Either file or text must be provided.")
    
    cv_text = ""
    filename = "text_input.txt"
    
    if file:
        filename = file.filename
        ext = os.path.splitext(filename)[1].lower()
        if ext not in [".pdf", ".txt"]:
            raise HTTPException(status_code=400, detail="Only .pdf and .txt files are supported.")
            
        try:
            # Create a temporary file to save the uploaded content
            with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
                content = await file.read()
                tmp.write(content)
                tmp_path = tmp.name
                
            if ext == ".pdf":
                cv_text = engine.extract_text_from_pdf(tmp_path)
            else:
                with open(tmp_path, "r", encoding="utf-8", errors="ignore") as f:
                    cv_text = f.read()
                    
            # Cleanup temp file
            os.unlink(tmp_path)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to process file: {str(e)}")
    else:
        cv_text = text

    if not cv_text.strip():
        raise HTTPException(status_code=400, detail="Extracted text is empty.")

    analysis = engine.analyze_resume(cv_text)
    analysis["filename"] = filename
    return JSONResponse(content=analysis)

@app.post("/match")
async def match_cv(request: MatchRequest):
    """Compares candidate CV details with Job Vacancy details and returns match percentage and feedback."""
    cv_data = {
        "skills_flat": request.cv_skills,
        "education": request.cv_education
    }
    match_result = engine.match_cv_to_job(cv_data, request.job_title, request.job_requirements)
    return JSONResponse(content=match_result)

@app.get("/", response_class=HTMLResponse)
async def get_interactive_ui():
    """Serves a premium, highly aesthetic web interface for testing the CV AI Analyzer."""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>CV AI Analyzer - BisaKerja</title>
        <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
        <script src="https://cdn.tailwindcss.com"></script>
        <script>
            tailwind.config = {
                theme: {
                    extend: {
                        fontFamily: {
                            sans: ['Outfit', 'sans-serif'],
                        }
                    }
                }
            }
        </script>
        <style>
            body {
                background: radial-gradient(circle at 50% 50%, #0c0a1a 0%, #030206 100%);
                background-attachment: fixed;
            }
            .glass {
                background: rgba(255, 255, 255, 0.02);
                backdrop-filter: blur(16px);
                -webkit-backdrop-filter: blur(16px);
                border: 1px solid rgba(255, 255, 255, 0.05);
            }
            .glass-panel {
                background: rgba(255, 255, 255, 0.03);
                backdrop-filter: blur(24px);
                -webkit-backdrop-filter: blur(24px);
                border: 1px solid rgba(255, 255, 255, 0.08);
            }
            @keyframes float {
                0%, 100% { transform: translateY(0px); }
                50% { transform: translateY(-12px); }
            }
            @keyframes float-slow {
                0%, 100% { transform: translateY(0px) scale(0.98); }
                50% { transform: translateY(8px) scale(1.02); }
            }
            .animate-float {
                animation: float 4s ease-in-out infinite;
            }
            .animate-float-slow {
                animation: float-slow 6s ease-in-out infinite;
            }
            .gradient-text {
                background: linear-gradient(135deg, #818cf8 0%, #c084fc 50%, #6366f1 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }
            /* Custom scrollbars */
            ::-webkit-scrollbar {
                width: 6px;
            }
            ::-webkit-scrollbar-track {
                background: rgba(0, 0, 0, 0.1);
            }
            ::-webkit-scrollbar-thumb {
                background: rgba(99, 102, 241, 0.3);
                border-radius: 4px;
            }
            ::-webkit-scrollbar-thumb:hover {
                background: rgba(99, 102, 241, 0.5);
            }
        </style>
    </head>
    <body class="text-slate-300 min-h-screen font-sans antialiased pb-16">
        <!-- Background decorative ambient lights -->
        <div class="absolute top-0 left-1/4 w-96 h-96 bg-indigo-600/10 rounded-full blur-[120px] pointer-events-none"></div>
        <div class="absolute bottom-1/4 right-1/4 w-96 h-96 bg-purple-600/10 rounded-full blur-[120px] pointer-events-none"></div>

        <!-- Custom Header -->
        <header class="w-full py-4 px-8 sticky top-0 z-50 glass backdrop-blur-md border-b border-white/5 bg-slate-950/40">
            <div class="max-w-6xl mx-auto flex items-center justify-between">
                <div class="flex items-center gap-3">
                    <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 flex items-center justify-center font-bold text-white text-xl shadow-[0_0_20px_rgba(99,102,241,0.4)]">B</div>
                    <div>
                        <h1 class="text-lg font-black tracking-tight text-white">CV AI <span class="gradient-text">Analyzer</span></h1>
                        <p class="text-[9px] text-indigo-400 font-bold uppercase tracking-wider">BisaKerja Premium Tools</p>
                    </div>
                </div>
                <div class="flex items-center gap-2">
                    <span class="px-2.5 py-0.5 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-[11px] font-semibold text-indigo-400">ATS Engine v1.2</span>
                    <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                </div>
            </div>
        </header>

        <!-- Main Workspace -->
        <main class="max-w-6xl mx-auto px-6 pt-12">
            <div class="grid grid-cols-1 lg:grid-cols-12 gap-12 items-start">
                
                <!-- Left: Title & Input Form -->
                <section class="lg:col-span-6 flex flex-col gap-8">
                    <div>
                        <!-- Pill Badge -->
                        <div class="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-xs font-semibold mb-5 shadow-sm">
                            <span class="w-1.5 h-1.5 rounded-full bg-indigo-400 inline-block animate-ping"></span>
                            <span>Akselerasi Karir Bersama AI</span>
                        </div>
                        
                        <!-- Heading -->
                        <h2 class="text-4xl lg:text-5xl font-black text-white leading-[1.15] tracking-tight mb-4">
                            Increase Your Chances <br/> of Passing <span class="gradient-text">CV ATS Screening by 73%</span>
                        </h2>
                        
                        <!-- Subheading -->
                        <p class="text-slate-400 text-sm leading-relaxed max-w-xl">
                            Analyze your CV with AI and get specific recommendations to increase your chances of passing ATS screening.
                        </p>
                    </div>

                    <!-- Main Form Card -->
                    <div class="glass-panel rounded-3xl p-8 shadow-2xl relative overflow-hidden">
                        <div class="absolute -top-12 -right-12 w-28 h-28 bg-indigo-500/5 rounded-full blur-2xl"></div>
                        
                        <div class="flex flex-col gap-6">
                            <!-- File Upload Area -->
                            <div>
                                <label class="block text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">Upload Your CV <span class="text-rose-500">*</span></label>
                                <div id="drop-zone" class="border-2 border-dashed border-slate-700/80 hover:border-indigo-500 bg-slate-950/20 hover:bg-indigo-500/5 rounded-2xl p-8 flex flex-col items-center justify-center gap-3 cursor-pointer transition-all duration-300 group">
                                    <input type="file" id="cv-file" class="hidden" accept=".pdf,.txt">
                                    <div class="w-12 h-12 rounded-full bg-slate-800/80 flex items-center justify-center group-hover:bg-indigo-600/20 group-hover:scale-110 transition-all duration-300 shadow-md">
                                        <svg class="w-6 h-6 text-slate-400 group-hover:text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"/>
                                        </svg>
                                    </div>
                                    <span class="text-sm font-bold text-slate-300" id="file-label">Click to upload or drag & drop</span>
                                    <span class="text-[11px] text-slate-500 font-semibold">PDF or TXT (Max 5MB)</span>
                                </div>
                            </div>

                            <!-- Target Roles Selector -->
                            <div>
                                <label class="block text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">Target Roles <span class="text-rose-500">*</span></label>
                                <div class="relative mb-3.5">
                                    <div class="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none">
                                        <svg class="w-4 h-4 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>
                                    </div>
                                    <input type="text" id="target-role" class="w-full bg-slate-950/40 border border-slate-800/80 focus:border-indigo-500 rounded-xl pl-10 pr-4 py-3 text-xs text-slate-200 outline-none placeholder:text-slate-600 transition-all font-medium" placeholder="Search roles (e.g., Product Designer, Data Analyst)">
                                </div>

                                <!-- Suggestions pills -->
                                <div>
                                    <span class="block text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-2">Suggested for you</span>
                                    <div class="flex flex-wrap gap-2" id="suggested-roles">
                                        <button class="role-btn px-3 py-1.5 rounded-lg bg-slate-900/60 hover:bg-indigo-600/20 text-[11.5px] font-bold text-slate-400 hover:text-indigo-400 border border-slate-800 hover:border-indigo-500/30 transition-all duration-200 cursor-pointer" data-role="Software Engineer">+ Software Engineer</button>
                                        <button class="role-btn px-3 py-1.5 rounded-lg bg-slate-900/60 hover:bg-indigo-600/20 text-[11.5px] font-bold text-slate-400 hover:text-indigo-400 border border-slate-800 hover:border-indigo-500/30 transition-all duration-200 cursor-pointer" data-role="Product Manager">+ Product Manager</button>
                                        <button class="role-btn px-3 py-1.5 rounded-lg bg-slate-900/60 hover:bg-indigo-600/20 text-[11.5px] font-bold text-slate-400 hover:text-indigo-400 border border-slate-800 hover:border-indigo-500/30 transition-all duration-200 cursor-pointer" data-role="Data Analyst">+ Data Analyst</button>
                                        <button class="role-btn px-3 py-1.5 rounded-lg bg-slate-900/60 hover:bg-indigo-600/20 text-[11.5px] font-bold text-slate-400 hover:text-indigo-400 border border-slate-800 hover:border-indigo-500/30 transition-all duration-200 cursor-pointer" data-role="UI/UX Designer">+ UI/UX Designer</button>
                                        <button class="role-btn px-3 py-1.5 rounded-lg bg-slate-900/60 hover:bg-indigo-600/20 text-[11.5px] font-bold text-slate-400 hover:text-indigo-400 border border-slate-800 hover:border-indigo-500/30 transition-all duration-200 cursor-pointer" data-role="Visual Designer">+ Visual Designer</button>
                                        <button class="role-btn px-3 py-1.5 rounded-lg bg-slate-900/60 hover:bg-indigo-600/20 text-[11.5px] font-bold text-slate-400 hover:text-indigo-400 border border-slate-800 hover:border-indigo-500/30 transition-all duration-200 cursor-pointer" data-role="Marketing Specialist">+ Marketing Specialist</button>
                                    </div>
                                </div>
                            </div>

                            <!-- Submit Button -->
                            <button id="btn-review" class="w-full py-4 mt-2 rounded-xl font-bold text-white text-xs bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 transition-all duration-300 uppercase tracking-widest shadow-[0_6px_24px_rgba(99,102,241,0.3)] hover:shadow-[0_8px_32px_rgba(99,102,241,0.5)] active:scale-[0.98] cursor-pointer">
                                Review Now
                            </button>
                        </div>
                    </div>
                </section>

                <!-- Right: Dynamic Panels (Mascot / Loading / Results) -->
                <section class="lg:col-span-6 flex flex-col gap-6 w-full lg:sticky lg:top-24">
                    
                    <!-- Panel 1: BisaKerja Statistics Mascot (Default) -->
                    <div id="panel-mascot" class="glass-panel rounded-3xl p-8 shadow-2xl flex flex-col items-center justify-center min-h-[460px] text-center relative overflow-hidden">
                        <!-- Floating ambient lights inside -->
                        <div class="absolute -bottom-16 -right-16 w-32 h-32 bg-purple-500/5 rounded-full blur-2xl"></div>
                        
                        <!-- Premium Animated Mascot SVG -->
                        <div class="w-64 h-64 relative flex items-center justify-center mb-6">
                            <svg class="w-full h-full animate-float" viewBox="0 0 200 200" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <!-- Glowing back drop -->
                                <circle cx="100" cy="100" r="70" fill="url(#mascotGlow)" opacity="0.25" />
                                
                                <!-- Antenna -->
                                <rect x="97" y="22" width="6" height="24" rx="3" fill="#a78bfa" />
                                <circle cx="100" cy="18" r="8" fill="#6366f1" />
                                <circle cx="100" cy="18" r="4" fill="#a78bfa" />
                                
                                <!-- Neck -->
                                <path d="M85 130 H115 L110 155 H90 L85 130 Z" fill="#1e1b4b" stroke="#312e81" stroke-width="2" />
                                
                                <!-- Ears -->
                                <rect x="42" y="75" width="8" height="30" rx="4" fill="#6366f1" />
                                <rect x="150" y="75" width="8" height="30" rx="4" fill="#6366f1" />
                                
                                <!-- Body/Shoulders -->
                                <path d="M60 155 H140 L130 185 H70 L60 155 Z" fill="url(#mascotBody)" stroke="#312e81" stroke-width="2" />
                                
                                <!-- Head Shield -->
                                <rect x="50" y="45" width="100" height="90" rx="32" fill="url(#mascotHead)" stroke="#4f46e5" stroke-width="3.5" />
                                
                                <!-- Screen Display -->
                                <rect x="62" y="57" width="76" height="64" rx="18" fill="#03001e" stroke="#1f1e3d" stroke-width="2" />
                                
                                <!-- Digital Glowing Eyes -->
                                <ellipse cx="84" cy="84" rx="7" ry="10" fill="#00f2fe" class="animate-pulse" />
                                <ellipse cx="116" cy="84" rx="7" ry="10" fill="#00f2fe" class="animate-pulse" />
                                
                                <!-- Mouth / Wave -->
                                <path d="M85 106 Q100 115 115 106" stroke="#00f2fe" stroke-width="3" stroke-linecap="round" fill="none" />
                                
                                <!-- Floating Stats Badges surrounding -->
                                <!-- Badge A: ATS 73% -->
                                <g class="animate-float-slow" transform="translate(130, 20)">
                                    <rect x="0" y="0" width="62" height="26" rx="8" fill="#10b981" />
                                    <text x="31" y="16" fill="white" font-family="Outfit" font-size="9" font-weight="bold" text-anchor="middle">ATS +73%</text>
                                </g>
                                <!-- Badge B: AI Score -->
                                <g class="animate-float" transform="translate(10, 115)">
                                    <circle cx="15" cy="15" r="15" fill="#3b82f6" />
                                    <path d="M10 15 L14 19 L21 11" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none" />
                                </g>
                                
                                <!-- Gradients Definition -->
                                <defs>
                                    <radialGradient id="mascotGlow" cx="50%" cy="50%" r="50%">
                                        <stop offset="0%" stop-color="#6366f1" />
                                        <stop offset="100%" stop-color="#6366f1" stop-opacity="0" />
                                    </radialGradient>
                                    <linearGradient id="mascotHead" x1="0%" y1="0%" x2="100%" y2="100%">
                                        <stop offset="0%" stop-color="#1e1e38" />
                                        <stop offset="100%" stop-color="#2d2b52" />
                                    </linearGradient>
                                    <linearGradient id="mascotBody" x1="0%" y1="0%" x2="100%" y2="100%">
                                        <stop offset="0%" stop-color="#121026" />
                                        <stop offset="100%" stop-color="#1e1b4b" />
                                    </linearGradient>
                                </defs>
                            </svg>
                        </div>
                        
                        <h3 class="text-lg font-extrabold text-white mb-2">BisaKerja Statistics Mascot</h3>
                        <p class="text-xs text-slate-400 max-w-sm mb-6 leading-relaxed">
                            Mascot kami siap membantu menganalisis CV Anda secara real-time. Unggah file CV Anda dan pilih target posisi untuk memulai proses audit.
                        </p>
                        
                        <!-- Simple stats row -->
                        <div class="grid grid-cols-3 gap-6 w-full max-w-sm border-t border-white/5 pt-6">
                            <div>
                                <p class="text-xl font-bold text-white leading-none">73%</p>
                                <p class="text-[10px] text-slate-500 uppercase font-bold mt-1 tracking-wider">Avg. Boost</p>
                            </div>
                            <div>
                                <p class="text-xl font-bold text-white leading-none">&lt; 3s</p>
                                <p class="text-[10px] text-slate-500 uppercase font-bold mt-1 tracking-wider">Speed</p>
                            </div>
                            <div>
                                <p class="text-xl font-bold text-white leading-none">100%</p>
                                <p class="text-[10px] text-slate-500 uppercase font-bold mt-1 tracking-wider">Secured</p>
                            </div>
                        </div>
                    </div>

                    <!-- Panel 2: Loading State (Hidden by default) -->
                    <div id="panel-loading" class="glass-panel rounded-3xl p-8 shadow-2xl flex flex-col items-center justify-center min-h-[460px] text-center hidden">
                        <div class="relative w-24 h-24 mb-6">
                            <!-- Glowing outer ring -->
                            <div class="absolute inset-0 rounded-full border-4 border-indigo-500/10 animate-pulse"></div>
                            <!-- Rotating dashed ring -->
                            <div class="absolute inset-0 rounded-full border-4 border-dashed border-indigo-500 border-t-transparent animate-spin"></div>
                            <!-- Core glow -->
                            <div class="absolute inset-4 rounded-full bg-gradient-to-br from-indigo-500 to-purple-500 opacity-80 shadow-[0_0_15px_rgba(99,102,241,0.5)] flex items-center justify-center">
                                <svg class="w-6 h-6 text-white animate-pulse" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M13 10V3L4 14h7v7l9-11h-7z"/>
                                </svg>
                            </div>
                        </div>
                        <h3 class="text-lg font-bold text-white mb-2" id="loading-header">Sedang Menganalisis...</h3>
                        <p class="text-xs text-slate-400 max-w-xs leading-relaxed" id="loading-text">
                            Kecerdasan Buatan sedang mengekstrak data dari file CV Anda. Mohon tunggu beberapa detik.
                        </p>
                    </div>

                    <!-- Panel 3: Results Dashboard (Hidden by default) -->
                    <div id="panel-results" class="glass-panel rounded-3xl p-6 shadow-2xl hidden relative">
                        
                        <!-- Card Header -->
                        <div class="flex justify-between items-center pb-4 border-b border-white/5 mb-6">
                            <div>
                                <h3 class="text-base font-extrabold text-white">Analisis Kecocokan ATS</h3>
                                <p class="text-[10px] text-indigo-400 font-bold uppercase tracking-wider mt-px" id="res-target-role">Software Engineer</p>
                            </div>
                            <button id="btn-reset" class="px-3.5 py-1.5 bg-slate-900 hover:bg-slate-800 border border-slate-800 rounded-lg text-xs font-bold text-slate-300 hover:text-white transition-all cursor-pointer">
                                Audit Ulang
                            </button>
                        </div>
                        
                        <!-- Core Match Stats Grid -->
                        <div class="grid grid-cols-1 md:grid-cols-12 gap-6 items-center mb-6">
                            
                            <!-- Score ring -->
                            <div class="md:col-span-5 flex flex-col items-center justify-center border-r border-white/5 pr-2">
                                <div class="relative w-32 h-32 flex items-center justify-center">
                                    <svg class="w-full h-full transform -rotate-90">
                                        <circle cx="64" cy="64" r="54" stroke="currentColor" stroke-width="7" class="text-slate-900" fill="transparent" />
                                        <circle cx="64" cy="64" r="54" stroke="currentColor" stroke-width="7" class="text-indigo-500" fill="transparent"
                                                id="match-circle" stroke-dasharray="339.29" stroke-dashoffset="339.29" stroke-linecap="round" style="transition: stroke-dashoffset 1s ease-in-out;" />
                                    </svg>
                                    <div class="absolute text-center">
                                        <span class="text-3xl font-black text-white leading-none" id="val-match-score">0%</span>
                                        <div class="text-[9px] text-slate-500 uppercase tracking-widest font-bold mt-1">Score</div>
                                    </div>
                                </div>
                                <div class="text-[11px] font-extrabold mt-3.5 uppercase tracking-wider text-indigo-400 text-center" id="val-match-cat">
                                    Recommended
                                </div>
                            </div>

                            <!-- Strengths & Recommendations -->
                            <div class="md:col-span-7 flex flex-col gap-4 pl-2">
                                <div>
                                    <h4 class="text-xs font-bold text-emerald-400 flex items-center gap-1.5 mb-1.5">
                                        <svg class="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                                        Kekuatan Utama CV
                                    </h4>
                                    <ul class="list-disc pl-5 text-[11.5px] text-slate-300 leading-relaxed flex flex-col gap-1" id="list-strengths">
                                        <!-- Will populate -->
                                    </ul>
                                </div>
                                <div>
                                    <h4 class="text-xs font-bold text-amber-400 flex items-center gap-1.5 mb-1.5">
                                        <svg class="w-4 h-4 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/></svg>
                                        Rekomendasi Perbaikan
                                    </h4>
                                    <ul class="list-disc pl-5 text-[11.5px] text-slate-300 leading-relaxed flex flex-col gap-1" id="list-recs">
                                        <!-- Will populate -->
                                    </ul>
                                </div>
                            </div>
                        </div>

                        <!-- Parse Profile Information -->
                        <div class="glass bg-slate-950/20 rounded-2xl p-4 mb-6 border border-white/5">
                            <h4 class="text-[11px] font-bold text-indigo-300 uppercase tracking-wider mb-3">Profil Terdeteksi</h4>
                            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                                <div>
                                    <label class="text-[9px] text-slate-500 font-bold uppercase tracking-wider block">Nama Lengkap</label>
                                    <span class="text-xs font-bold text-white block mt-0.5 truncate" id="out-name">-</span>
                                </div>
                                <div>
                                    <label class="text-[9px] text-slate-500 font-bold uppercase tracking-wider block">Email</label>
                                    <span class="text-xs font-bold text-white block mt-0.5 truncate" id="out-email">-</span>
                                </div>
                                <div>
                                    <label class="text-[9px] text-slate-500 font-bold uppercase tracking-wider block">Telepon</label>
                                    <span class="text-xs font-bold text-white block mt-0.5 truncate" id="out-phone">-</span>
                                </div>
                                <div>
                                    <label class="text-[9px] text-slate-500 font-bold uppercase tracking-wider block">Pendidikan</label>
                                    <span class="text-xs font-bold text-white block mt-0.5 truncate" id="out-education">-</span>
                                </div>
                            </div>
                        </div>

                        <!-- Skill comparison lists -->
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4 border-t border-white/5">
                            <div>
                                <label class="text-[10px] text-slate-500 font-bold uppercase tracking-wider block mb-2">Keahlian yang Terpenuhi</label>
                                <div class="flex flex-wrap gap-1.5" id="val-matched-skills">
                                    <!-- Populate pills -->
                                </div>
                            </div>
                            <div>
                                <label class="text-[10px] text-slate-500 font-bold uppercase tracking-wider block mb-2">Keahlian yang Perlu Ditambahkan</label>
                                <div class="flex flex-wrap gap-1.5" id="val-missing-skills">
                                    <!-- Populate pills -->
                                </div>
                            </div>
                        </div>

                    </div>

                </section>
            </div>
        </main>

        <script>
            // Predefined role requirements maps
            const roleRequirements = {
                "Software Engineer": "Kualifikasi:\\n- Menguasai bahasa pemrograman seperti JavaScript, TypeScript, Python, atau Java\\n- Mengerti framework web modern seperti React, Next.js, Node.js, atau Spring Boot\\n- Berpengalaman menggunakan Git/GitHub dan REST API\\n- Menguasai database SQL (PostgreSQL, MySQL) atau NoSQL (MongoDB)\\n- Memahami konsep clean code, testing, dan cloud deployment (AWS/Docker)",
                "Product Manager": "Kualifikasi:\\n- Memiliki pemahaman kuat tentang product lifecycle, market research, dan product strategy\\n- Berpengalaman dalam merancang Product Requirement Document (PRD) dan roadmap produk\\n- Berpengalaman menggunakan metodologi Agile/Scrum\\n- Kemampuan komunikasi yang sangat baik untuk kolaborasi lintas divisi\\n- Berjiwa leadership dan memiliki analytical skills yang tajam",
                "Data Analyst": "Kualifikasi:\\n- Menguasai SQL untuk pengambilan data dari database\\n- Mahir pemrograman Python (pandas, numpy) atau R untuk analisis data\\n- Berpengalaman menggunakan data visualization tools seperti Tableau, PowerBI, atau Looker Studio\\n- Memahami analisis statistik, AB testing, dan pengolahan data besar\\n- Kemampuan menyajikan insight data secara bisnis",
                "UI/UX Designer": "Kualifikasi:\\n- Mahir menggunakan Figma untuk wireframing, prototyping, dan design system\\n- Memahami user research, usability testing, dan user flow\\n- Memiliki pengetahuan tentang design principles, responsive design, dan mobile UI\\n- Berpengalaman berkolaborasi dengan tim developer\\n- Portofolio desain UI/UX yang kuat dan berorientasi pada pengguna",
                "Visual Designer": "Kualifikasi:\\n- Mahir menggunakan tools desain seperti Adobe Photoshop, Illustrator, atau Figma\\n- Memiliki selera visual yang tinggi dalam typography, layout, dan branding\\n- Berpengalaman membuat aset visual untuk media sosial, website, dan marketing campaign\\n- Mampu menerjemahkan brief kreatif menjadi karya visual yang menarik\\n- Portofolio portofolio desain grafis/visual yang kreatif",
                "Marketing Specialist": "Kualifikasi:\\n- Memahami dasar digital marketing, SEO/SEM, dan social media marketing\\n- Berpengalaman mengelola campaign iklan (Google Ads, Meta Ads)\\n- Terbiasa menggunakan analytics tools seperti Google Analytics\\n- Memiliki copywriting dan content creation yang baik\\n- Mampu menganalisis performa campaign dan ROI pemasaran"
            };

            function getRequirementsForRole(role) {
                const keys = Object.keys(roleRequirements);
                const matchedKey = keys.find(k => k.toLowerCase() === role.toLowerCase().trim());
                if (matchedKey) {
                    return roleRequirements[matchedKey];
                }
                // Fallback for custom entries
                return `Kualifikasi:\\n- Berpengalaman di bidang ${role} atau posisi terkait\\n- Memiliki pemahaman tentang best practices posisi ${role}\\n- Menguasai tool dan teknologi standard industri yang relevan\\n- Memiliki kemampuan kolaborasi dan pemecahan masalah yang baik`;
            }

            // Elements
            const dropZone = document.getElementById('drop-zone');
            const fileInput = document.getElementById('cv-file');
            const fileLabel = document.getElementById('file-label');
            const targetRoleInput = document.getElementById('target-role');
            const btnReview = document.getElementById('btn-review');
            
            const panelMascot = document.getElementById('panel-mascot');
            const panelLoading = document.getElementById('panel-loading');
            const panelResults = document.getElementById('panel-results');
            
            const loadingHeader = document.getElementById('loading-header');
            const loadingText = document.getElementById('loading-text');
            const btnReset = document.getElementById('btn-reset');

            // Drag and Drop implementation
            dropZone.addEventListener('click', () => fileInput.click());
            dropZone.addEventListener('dragover', (e) => {
                e.preventDefault();
                dropZone.classList.add('border-indigo-500', 'bg-indigo-500/5');
            });
            dropZone.addEventListener('dragleave', () => {
                dropZone.classList.remove('border-indigo-500', 'bg-indigo-500/5');
            });
            dropZone.addEventListener('drop', (e) => {
                e.preventDefault();
                dropZone.classList.remove('border-indigo-500', 'bg-indigo-500/5');
                if (e.dataTransfer.files.length) {
                    fileInput.files = e.dataTransfer.files;
                    updateFileLabel();
                }
            });
            fileInput.addEventListener('change', updateFileLabel);

            function updateFileLabel() {
                if (fileInput.files.length) {
                    fileLabel.textContent = fileInput.files[0].name;
                    fileLabel.classList.remove('text-slate-300');
                    fileLabel.classList.add('text-indigo-400');
                } else {
                    fileLabel.textContent = "Click to upload or drag & drop";
                    fileLabel.classList.remove('text-indigo-400');
                    fileLabel.classList.add('text-slate-300');
                }
            }

            // Suggestions handling
            document.querySelectorAll('.role-btn').forEach(btn => {
                btn.addEventListener('click', () => {
                    const role = btn.getAttribute('data-role');
                    targetRoleInput.value = role;
                    
                    // Highlight selected suggested role button
                    document.querySelectorAll('.role-btn').forEach(b => {
                        b.classList.remove('bg-indigo-600/20', 'text-indigo-400', 'border-indigo-500/30');
                        b.classList.add('bg-slate-900/60', 'text-slate-400', 'border-slate-800');
                    });
                    btn.classList.add('bg-indigo-600/20', 'text-indigo-400', 'border-indigo-500/30');
                    btn.classList.remove('bg-slate-900/60', 'text-slate-400', 'border-slate-800');
                });
            });

            // Review Now execution flow
            btnReview.addEventListener('click', async () => {
                const hasFile = fileInput.files.length > 0;
                const targetRole = targetRoleInput.value.trim();

                if (!hasFile) {
                    alert("Mohon unggah file CV Anda terlebih dahulu.");
                    return;
                }
                if (!targetRole) {
                    alert("Mohon isi atau pilih Target Role terlebih dahulu.");
                    return;
                }

                // Show loading
                panelMascot.classList.add('hidden');
                panelResults.classList.add('hidden');
                panelLoading.classList.remove('hidden');
                
                loadingHeader.textContent = "Sedang Mengekstrak CV...";
                loadingText.textContent = "Mengidentifikasi informasi data pribadi dan keahlian menggunakan model NLP.";

                // Step 1: Call /analyze
                const formData = new FormData();
                formData.append('file', fileInput.files[0]);

                try {
                    const analyzeRes = await fetch('/analyze', {
                        method: 'POST',
                        body: formData
                    });

                    if (!analyzeRes.ok) {
                        const err = await analyzeRes.json();
                        throw new Error(err.detail || "Gagal memproses ekstraksi CV.");
                    }

                    const cvData = await analyzeRes.json();

                    // Step 2: Call /match
                    loadingHeader.textContent = "Mengevaluasi Kualifikasi...";
                    loadingText.textContent = `Mencocokkan daftar keahlian Anda dengan persyaratan posisi ${targetRole}.`;

                    const jobReqs = getRequirementsForRole(targetRole);

                    const matchRes = await fetch('/match', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            cv_skills: cvData.skills_flat,
                            cv_education: cvData.education,
                            job_title: targetRole,
                            job_requirements: jobReqs
                        })
                    });

                    if (!matchRes.ok) {
                        const err = await matchRes.json();
                        throw new Error(err.detail || "Gagal mencocokkan data lowongan.");
                    }

                    const matchData = await matchRes.json();

                    // Step 3: Populate and render results dashboard
                    renderResults(cvData, matchData, targetRole);

                    // Show Results
                    panelLoading.classList.add('hidden');
                    panelResults.classList.remove('hidden');

                } catch (error) {
                    panelLoading.classList.add('hidden');
                    panelMascot.classList.remove('hidden');
                    alert("Error: " + error.message);
                }
            });

            // Audit Reset
            btnReset.addEventListener('click', () => {
                panelResults.classList.add('hidden');
                panelMascot.classList.remove('hidden');
                
                // Clear inputs
                fileInput.value = "";
                updateFileLabel();
                targetRoleInput.value = "";
                document.querySelectorAll('.role-btn').forEach(b => {
                    b.classList.remove('bg-indigo-600/20', 'text-indigo-400', 'border-indigo-500/30');
                    b.classList.add('bg-slate-900/60', 'text-slate-400', 'border-slate-800');
                });
            });

            // Results Render Engine
            function renderResults(cvData, matchData, role) {
                // Header details
                document.getElementById('res-target-role').textContent = role;

                // Circular Score Progress
                const score = matchData.match_percentage;
                document.getElementById('val-match-score').textContent = score + "%";
                document.getElementById('val-match-cat').textContent = matchData.match_category;

                const circle = document.getElementById('match-circle');
                const circumference = 2 * Math.PI * 54; // 339.29
                const offset = circumference - (score / 100) * circumference;
                circle.style.strokeDashoffset = offset;

                // Color score ring & status
                const catText = document.getElementById('val-match-cat');
                if (score >= 80) {
                    circle.setAttribute('class', 'text-emerald-500');
                    catText.className = "text-[11px] font-extrabold mt-3.5 uppercase tracking-wider text-emerald-400 text-center";
                } else if (score >= 60) {
                    circle.setAttribute('class', 'text-amber-500');
                    catText.className = "text-[11px] font-extrabold mt-3.5 uppercase tracking-wider text-amber-400 text-center";
                } else {
                    circle.setAttribute('class', 'text-rose-500');
                    catText.className = "text-[11px] font-extrabold mt-3.5 uppercase tracking-wider text-rose-400 text-center";
                }

                // Strengths
                const strengthsList = document.getElementById('list-strengths');
                strengthsList.innerHTML = "";
                matchData.strengths.forEach(str => {
                    const li = document.createElement('li');
                    li.textContent = str;
                    strengthsList.appendChild(li);
                });
                if (!matchData.strengths.length) {
                    strengthsList.innerHTML = "<li>Tidak ada kelebihan spesifik yang tercatat.</li>";
                }

                // Recommendations
                const recsList = document.getElementById('list-recs');
                recsList.innerHTML = "";
                matchData.recommendations.forEach(rec => {
                    const li = document.createElement('li');
                    li.textContent = rec;
                    recsList.appendChild(li);
                });
                if (!matchData.recommendations.length) {
                    recsList.innerHTML = "<li>Kualifikasi sudah cukup optimal untuk posisi ini.</li>";
                }

                // Parsed Profile Info
                document.getElementById('out-name').textContent = cvData.name || "-";
                document.getElementById('out-email').textContent = cvData.email || "-";
                document.getElementById('out-phone').textContent = cvData.phone || "-";
                document.getElementById('out-education').textContent = cvData.education || "-";

                // Matched Skills tags
                const matchedContainer = document.getElementById('val-matched-skills');
                matchedContainer.innerHTML = "";
                matchData.matched_skills.forEach(skill => {
                    const span = document.createElement('span');
                    span.className = "px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20";
                    span.textContent = skill;
                    matchedContainer.appendChild(span);
                });
                if (!matchData.matched_skills.length) {
                    matchedContainer.innerHTML = '<span class="text-xs text-slate-600">Tidak ada skill yang cocok</span>';
                }

                // Missing Skills tags
                const missingContainer = document.getElementById('val-missing-skills');
                missingContainer.innerHTML = "";
                matchData.missing_skills.forEach(skill => {
                    const span = document.createElement('span');
                    span.className = "px-2 py-0.5 rounded text-[10px] font-bold bg-rose-500/10 text-rose-400 border border-rose-500/20";
                    span.textContent = skill;
                    missingContainer.appendChild(span);
                });
                if (!matchData.missing_skills.length) {
                    missingContainer.innerHTML = '<span class="text-xs text-slate-600">Semua keahlian terpenuhi</span>';
                }
            }
        </script>
    </body>
    </html>
    """
    return html_content