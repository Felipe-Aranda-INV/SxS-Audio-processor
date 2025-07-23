import streamlit as st
import io
import re
import wave
import librosa
import soundfile as sf
from datetime import datetime
import tempfile
import os
from typing import List, Optional, Tuple, Dict, Any

# Configure page
st.set_page_config(
    page_title="SxS Audio Evaluation System",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for consistent styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(90deg, #1a1a2e 0%, #16213e 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    
    .step-indicator {
        display: flex;
        justify-content: space-between;
        margin: 2rem 0;
        padding: 1rem;
        background-color: #16213e;
        border-radius: 10px;
        color: white;
    }
    
    .step {
        text-align: center;
        padding: 0.5rem;
        border-radius: 5px;
        font-weight: bold;
        flex: 1;
        margin: 0 0.25rem;
    }
    
    .step.active {
        background-color: #4285f4;
        color: white;
    }
    
    .step.completed {
        background-color: #34a853;
        color: white;
    }
    
    .upload-section {
        border: 2px dashed #71b280;
        border-radius: 10px;
        padding: 2rem;
        text-align: center;
        margin: 1rem 0;
        background-color: #DCF58F;
        color: black;
    }
    
    .gemini-section {
        border: 2px dashed #4285f4;
        border-radius: 10px;
        padding: 2rem;
        text-align: center;
        margin: 1rem 0;
        background-color: #e3f2fd;
        color: #0d47a1;
    }
    
    .chatgpt-section {
        border: 2px dashed #10a37f;
        border-radius: 10px;
        padding: 2rem;
        text-align: center;
        margin: 1rem 0;
        background-color: #e8f5e8;
        color: #1b5e20;
    }
    
    .success-message {
        background-color: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
        border: 1px solid #c3e6cb;
    }
    
    .error-message {
        background-color: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
        border: 1px solid #f5c6cb;
    }
    
    .warning-message {
        background-color: #fff3cd;
        color: #856404;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
        border: 1px solid #ffeaa7;
    }
    
    .info-card {
        background-color: #e3f2fd;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #2196f3;
        margin: 1rem 0;
        color: #0d47a1;
    }
    
    .stats-container {
        display: flex;
        justify-content: space-around;
        margin: 2rem 0;
    }
    
    .stat-card {
        text-align: center;
        padding: 1rem;
        background-color: #DCF58F;
        color: black;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        flex: 1;
        margin: 0 0.5rem;
    }
    
    .navigation-tip {
        background-color: #ffecd2;
        color: #856404;
        padding: 0.8rem;
        border-radius: 5px;
        margin: 1rem 0;
        border: 1px solid #ffeaa7;
        font-size: 0.9rem;
    }
    
    /* Custom Step 3 Form Styling */
    .custom-form-container {
        background-color: #16213e;
        color: white;
        padding: 0.5rem;
        border-radius: 15px;
        margin: 0.5rem 0;
        box-shadow: 0 8px 16px rgba(0,0,0,0.3);
    }
    
    .form-row {
        display: flex;
        align-items: center;
        margin-bottom: 1.5rem;
        padding: 0.75rem 0;
        border-bottom: 1px solid rgba(255,255,255,0.1);
    }
    
    .form-row:last-child {
        border-bottom: none;
        justify-content: center;
        padding-top: 2rem;
    }
    
    .form-label {
        font-weight: 600;
        margin-right: 1rem;
        min-width: 140px;
        color: #e3f2fd;
    }
    
    .form-value {
        flex-grow: 1;
        padding: 0.5rem 0.75rem;
        background-color: rgba(255,255,255,0.1);
        border: 1px solid rgba(255,255,255,0.2);
        border-radius: 6px;
        color: white;
        margin-right: 1rem;
    }
    
    .form-value.readonly {
        background-color: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.1);
        cursor: not-allowed;
    }
    
    .validation-status {
        display: flex;
        align-items: center;
        margin-left: 1rem;
        font-size: 0.9rem;
    }
    
    .validation-pending {
        color: #ffa726;
    }
    
    .validation-success {
        color: #66bb6a;
    }
    
    .validation-error {
        color: #ef5350;
    }
    
    .audio-info {
        display: flex;
        align-items: center;
        background-color: rgba(255,255,255,0.1);
        padding: 0.75rem;
        border-radius: 8px;
        margin-right: 1rem;
        flex-grow: 1;
    }
    
    .audio-icon {
        font-size: 2rem;
        margin-right: 1rem;
        color: #4285f4;
    }
    
    .load-button {
        background-color: #4285f4;
        color: white;
        border: none;
        padding: 0.75rem 1.5rem;
        border-radius: 6px;
        cursor: pointer;
        font-weight: 600;
        transition: background-color 0.3s;
        margin-left: 1rem;
    }
    
    .load-button:hover {
        background-color: #3367d6;
    }
    
    .load-button:disabled {
        background-color: #666;
        cursor: not-allowed;
    }
    
    .submit-button {
        background-color: #34a853;
        color: white;
        border: none;
        padding: 1rem 3rem;
        border-radius: 8px;
        cursor: pointer;
        font-weight: 600;
        font-size: 1.1rem;
        transition: background-color 0.3s;
    }
    
    .submit-button:hover {
        background-color: #2d8a47;
    }
    
    .submit-button:disabled {
        background-color: #666;
        cursor: not-allowed;
    }
    
    .drive-url-container {
        display: flex;
        align-items: center;
        flex-grow: 1;
    }
    
    .drive-url-display {
        flex-grow: 1;
        padding: 0.5rem 0.75rem;
        background-color: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 6px;
        color: #aaa;
        font-style: italic;
        margin-right: 1rem;
    }
    
    .drive-url-ready {
        background-color: rgba(76, 175, 80, 0.2);
        border: 1px solid rgba(76, 175, 80, 0.3);
        color: #81c784;
        font-style: normal;
    }
</style>
""", unsafe_allow_html=True)

# Constants for validation
ALLOWED_LANGUAGES = [
    "id-ID", "ar-EG", "ko-KR", "es-419", "pt-BR", "hi-IN", "en-IN", "ja-JP",
    "hi-EN", "ko-EN", "id-EN", "vi-VN", "pt-EN", "de-DE", "fr-FR", "zh-CN",
    "nl-NL", "ru-EN", "ja-KR", "es-EN", "zh-TW", "ar-EN", "zh-EN", "fr-EN",
    "ja-EN", "de-EN", "ko-JA", "ko-ZH", "es-en"
]

PROJECT_TYPES = ["Monolingual", "Audio Out", "Mixed", "Language Learning"]

MODEL_COMBINATIONS = [
    ("Gemini", "ChatGPT"),
    ("ChatGPT", "Gemini")
]

MIN_AUDIO_DURATION = 60.0

class AudioFileValidator:
    """Production-grade audio file validator for SxS model evaluation."""
    
    def __init__(self):
        self.supported_formats = ['.wav', '.mp3', '.m4a', '.flac', '.ogg', '.aac']
        self.temp_files = []
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
    
    def cleanup(self):
        """Clean up temporary files"""
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
            except Exception as e:
                st.warning(f"Could not clean up temp file: {e}")
        self.temp_files = []
    
    def validate_audio_file(self, audio_file) -> Dict[str, Any]:
        """Comprehensive audio file validation."""
        result = {
            'is_valid': False,
            'duration': 0.0,
            'sample_rate': 0,
            'channels': 0,
            'format': '',
            'errors': [],
            'warnings': []
        }
        
        try:
            audio_file.seek(0)
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f"_{audio_file.name}")
            temp_file.write(audio_file.read())
            temp_file.close()
            
            self.temp_files.append(temp_file.name)
            
            if not os.path.exists(temp_file.name) or os.path.getsize(temp_file.name) == 0:
                result['errors'].append("Audio file is empty or corrupted")
                return result
            
            try:
                audio_data, sample_rate = librosa.load(temp_file.name, sr=None)
                duration = len(audio_data) / sample_rate
                
                result['duration'] = duration
                result['sample_rate'] = sample_rate
                result['format'] = os.path.splitext(audio_file.name)[1].lower()
                
                if len(audio_data) == 0:
                    result['errors'].append("Audio file contains no readable audio data")
                    return result
                
                if duration < 1.0:
                    result['errors'].append("Audio duration is less than 1 second")
                    return result
                
                if duration < MIN_AUDIO_DURATION:
                    result['warnings'].append(f"Audio duration ({duration:.1f}s) is below recommended minimum ({MIN_AUDIO_DURATION}s)")
                
                try:
                    with sf.SoundFile(temp_file.name) as f:
                        result['channels'] = f.channels
                        test_frames = f.read(1024)
                        if len(test_frames) == 0:
                            result['errors'].append("Cannot read audio frames from file")
                            return result
                except Exception as sf_error:
                    result['warnings'].append(f"Secondary format validation warning: {str(sf_error)}")
                
                result['is_valid'] = True
                
            except Exception as librosa_error:
                result['errors'].append(f"Audio loading failed: {str(librosa_error)}")
                
                try:
                    with wave.open(temp_file.name, 'rb') as wav_file:
                        frames = wav_file.getnframes()
                        sample_rate = wav_file.getframerate()
                        channels = wav_file.getnchannels()
                        
                        duration = frames / sample_rate
                        
                        result['duration'] = duration
                        result['sample_rate'] = sample_rate
                        result['channels'] = channels
                        result['format'] = '.wav'
                        
                        if duration >= 1.0:
                            result['is_valid'] = True
                            result['warnings'].append("Validated using fallback WAV reader")
                        
                except Exception as wav_error:
                    result['errors'].append(f"Fallback validation also failed: {str(wav_error)}")
            
        except Exception as e:
            result['errors'].append(f"Unexpected validation error: {str(e)}")
        
        return result
    
    def placeholder_transcription_validation(self, audio_file, expected_language: str = None) -> Dict[str, Any]:
        """PLACEHOLDER: Future transcription validation functionality."""
        placeholder_result = {
            'transcription_available': False,
            'transcription_text': '',
            'language_detected': expected_language or 'unknown',
            'confidence_score': 0.0,
            'quality_metrics': {
                'clarity_score': 0.0,
                'noise_level': 0.0,
                'speech_to_noise_ratio': 0.0
            },
            'validation_status': 'PLACEHOLDER_NOT_IMPLEMENTED',
            'expected_language': expected_language
        }
        
        return placeholder_result

def parse_question_id(question_id: str) -> Tuple[Optional[str], Optional[str]]:
    """Parse Question ID to extract language and project type using regex patterns."""
    language = None
    project_type = None
    
    try:
        language_pattern = r'human_eval_([a-z]{2}-[A-Z]{2}|[a-z]{2}-\d{3}|[a-z]{2}-[a-z]{2})\+INTERNAL'
        language_match = re.search(language_pattern, question_id)
        
        if language_match:
            extracted_lang = language_match.group(1)
            if extracted_lang in ALLOWED_LANGUAGES:
                language = extracted_lang
        
        project_type_mapping = {
            'monolingual': 'Monolingual',
            'audio_out': 'Audio Out',
            'mixed': 'Mixed',
            'code_mixed': 'Mixed',
            'language_learning': 'Language Learning'
        }
        
        project_pattern = r'experience_([a-z_]+)_human_eval'
        project_match = re.search(project_pattern, question_id)
        
        if project_match:
            extracted_project = project_match.group(1)
            for key, value in project_type_mapping.items():
                if key in extracted_project:
                    project_type = value
                    break
        
    except Exception as e:
        st.warning(f"Error parsing Question ID: {e}")
    
    return language, project_type

def validate_email_format(email: str) -> bool:
    """Validate email format"""
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_pattern, email) is not None

def get_step_status(current_page: str) -> List[str]:
    """Get the status of each step based on session state"""
    steps = ["1️⃣ Metadata & Audio", "2️⃣ Audio Verification", "3️⃣ Summary & Submission"]
    statuses = []
    
    for i, step in enumerate(steps):
        if step.endswith(current_page):
            statuses.append("active")
        else:
            if step.endswith("Metadata & Audio") and is_step_completed("Metadata & Audio"):
                statuses.append("completed")
            elif step.endswith("Audio Verification") and is_step_completed("Audio Verification"):
                statuses.append("completed")
            elif step.endswith("Summary & Submission") and is_step_completed("Summary & Submission"):
                statuses.append("completed")
            else:
                statuses.append("")
    
    return statuses

def display_step_indicator(current_page: str):
    """Display the step indicator"""
    steps = ["1️⃣ Metadata & Audio", "2️⃣ Audio Verification", "3️⃣ Summary & Submission"]
    
    if current_page == "Help":
        return
    
    statuses = get_step_status(current_page)
    
    step_html = '<div class="step-indicator">'
    for step, status in zip(steps, statuses):
        step_html += f'<div class="step {status}">{step}</div>'
    step_html += '</div>'
    
    st.markdown(step_html, unsafe_allow_html=True)

def is_step_completed(step_name: str) -> bool:
    """Check if a step is completed based on session state"""
    if step_name == "Metadata & Audio":
        metadata_complete = all(key in st.session_state and st.session_state[key] for key in 
                               ['question_id', 'initial_goal', 'prompt_text', 'model1', 'model2', 'metadata_saved'])
        audio_complete = all(key in st.session_state and st.session_state[key] for key in 
                           ['model1_audio_files', 'model2_audio_files', 'audio_saved'])
        return metadata_complete and audio_complete
    elif step_name == "Audio Verification":
        return ('audio_verification_complete' in st.session_state and 
                st.session_state.audio_verification_complete and
                'verification_results' in st.session_state)
    elif step_name == "Summary & Submission":
        return st.session_state.get('submission_complete', False)
    return False

def get_next_step(current_page: str) -> Optional[str]:
    """Get the next step in the workflow"""
    steps = ["Metadata & Audio", "Audio Verification", "Summary & Submission"]
    try:
        current_index = steps.index(current_page)
        if current_index < len(steps) - 1:
            return steps[current_index + 1]
    except ValueError:
        pass
    return None

def show_next_step_button(current_page: str):
    """Show the next step button if current step is completed"""
    if not is_step_completed(current_page):
        return
        
    next_step = get_next_step(current_page)
    if not next_step:
        return
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        next_step_emoji = {
            "Audio Verification": "2️⃣",
            "Summary & Submission": "3️⃣"
        }
        button_text = f"Continue to {next_step_emoji.get(next_step, '▶️')} {next_step}"
        
        if st.button(button_text, type="primary", use_container_width=True, key=f"next_to_{next_step}"):
            st.session_state.current_page = next_step
            st.rerun()

def validate_email_against_spreadsheet(email: str) -> bool:
    """PLACEHOLDER: Email validation against authorized users spreadsheet."""
    return "@" in email and any(email.endswith(domain) for domain in [".com", ".org", ".net", ".edu"])

def generate_drive_url_placeholder(audio_data: Dict[str, Any], filename: str, metadata: dict) -> str:
    """PLACEHOLDER: Upload audio validation results to Google Drive and return shareable URL."""
    return f"https://drive.google.com/file/d/PLACEHOLDER_AUDIO_VALIDATION_ID/view?usp=sharing"

def submit_to_spreadsheet_placeholder(form_data: Dict[str, Any]) -> bool:
    """PLACEHOLDER: Submit form data to Google Sheets tracking tab."""
    return True

def main():
    # Initialize current page in session state
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "Metadata & Audio"
    
    # Initialize form state variables
    if 'metadata_saved' not in st.session_state:
        st.session_state.metadata_saved = False
    if 'audio_saved' not in st.session_state:
        st.session_state.audio_saved = False
    if 'email_validated' not in st.session_state:
        st.session_state.email_validated = False
    if 'drive_url_generated' not in st.session_state:
        st.session_state.drive_url_generated = False
    if 'drive_url' not in st.session_state:
        st.session_state.drive_url = ""
    if 'user_email' not in st.session_state:
        st.session_state.user_email = ""
    if 'audio_verification_complete' not in st.session_state:
        st.session_state.audio_verification_complete = False
    if 'submission_complete' not in st.session_state:
        st.session_state.submission_complete = False
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🎵 SxS Audio Model Evaluation System</h1>
        <p>Side-by-Side audio evaluation for Gemini vs ChatGPT model comparison</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar navigation
    st.sidebar.title("🧭 Navigation")
    
    nav_options = [
        "1️⃣ Metadata & Audio",
        "2️⃣ Audio Verification",
        "3️⃣ Summary & Submission",
        "❓ Help"
    ]
    
    page_mapping = {
        "1️⃣ Metadata & Audio": "Metadata & Audio",
        "2️⃣ Audio Verification": "Audio Verification",
        "3️⃣ Summary & Submission": "Summary & Submission",
        "❓ Help": "Help"
    }
    
    # Find current selection for radio
    current_nav_selection = None
    for nav_option, page_name in page_mapping.items():
        if page_name == st.session_state.current_page:
            current_nav_selection = nav_option
            break
    
    if current_nav_selection is None:
        current_nav_selection = "1️⃣ Metadata & Audio"
    
    # Display navigation with status and validation
    selected_nav = st.sidebar.radio(
        "Choose Step:",
        nav_options,
        index=nav_options.index(current_nav_selection) if current_nav_selection in nav_options else 0,
        format_func=lambda x: f"{x} {'✅' if is_step_completed(page_mapping[x]) else ''}"
    )
    
    # Update session state based on selection with validation
    requested_page = page_mapping[selected_nav]
    
    # Validate step access
    if requested_page == "Audio Verification" and not is_step_completed("Metadata & Audio"):
        st.sidebar.warning("⚠️ Complete Step 1 first")
        requested_page = "Metadata & Audio"
    elif requested_page == "Summary & Submission" and not is_step_completed("Audio Verification"):
        st.sidebar.warning("⚠️ Complete Step 2 first")
        requested_page = "Audio Verification"
    
    st.session_state.current_page = requested_page
    page = requested_page
    
    # Navigation tips
    st.sidebar.markdown("""
    <div class="navigation-tip">
        💡 <strong>Navigation Tip:</strong><br>
        Complete each step to unlock the next one. Upload audio recordings for both models for side-by-side comparison!
    </div>
    """, unsafe_allow_html=True)
    
    # Session info in sidebar
    if 'question_id' in st.session_state:
        st.sidebar.markdown("### 📋 Current Session")
        st.sidebar.info(f"**ID:** {st.session_state.question_id[:20]}...")
        if 'model1' in st.session_state and 'model2' in st.session_state:
            st.sidebar.info(f"**Models:** {st.session_state.model1} vs {st.session_state.model2}")
        if 'detected_language' in st.session_state and st.session_state.detected_language:
            st.sidebar.info(f"**Language:** {st.session_state.detected_language}")
        if 'detected_project_type' in st.session_state and st.session_state.detected_project_type:
            st.sidebar.info(f"**Project:** {st.session_state.detected_project_type}")
    
    # Session stats
    if any(key in st.session_state for key in ['model1_audio_files', 'model2_audio_files']):
        st.sidebar.markdown("### 📊 Session Stats")
        if 'model1_audio_files' in st.session_state and st.session_state.model1_audio_files:
            st.sidebar.metric("Model 1 Audio Files", len(st.session_state.model1_audio_files))
        if 'model2_audio_files' in st.session_state and st.session_state.model2_audio_files:
            st.sidebar.metric("Model 2 Audio Files", len(st.session_state.model2_audio_files))
    
    # Display step indicator
    display_step_indicator(page)
    
    # Page content
    if page == "Metadata & Audio":
        st.header("1️⃣ Metadata & Audio Recordings")
        
        st.markdown("""
        <div class="info-card">
            <h4>📋 Required Information</h4>
            <p>Please provide the basic information and audio recordings for your side-by-side evaluation. Complete each section separately.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # SECTION 1: Metadata Form
        st.subheader("📝 Metadata Information")
        
        with st.form("metadata_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                question_id = st.text_input(
                    "Question ID *",
                    placeholder="e.g., 30aeeee4a88e5dd6e04a0c5fd0400b4a+bard_data+coach_P128214...",
                    help="Enter the unique identifier for this comparison",
                    value=st.session_state.get('question_id', '')
                )
                
                model_combo = st.selectbox(
                    "Select Model Combination *",
                    options=MODEL_COMBINATIONS,
                    format_func=lambda x: f"{x[0]} vs {x[1]}",
                    help="Choose the models being compared",
                    index=0 if 'model1' not in st.session_state else next(
                        (i for i, combo in enumerate(MODEL_COMBINATIONS) 
                         if combo[0] == st.session_state.get('model1') and combo[1] == st.session_state.get('model2')), 0)
                )
            
            with col2:
                initial_goal = st.text_area(
                    "Initial Goal *",
                    placeholder="Describe the goal of this evaluation task...",
                    height=100,
                    help="The main objective of this audio evaluation",
                    value=st.session_state.get('initial_goal', '')
                )
                
                prompt_text = st.text_area(
                    "Initial Prompt *",
                    placeholder="Enter the prompt used for both models...",
                    height=100,
                    help="The prompt that was given to both models",
                    value=st.session_state.get('prompt_text', '')
                )
            
            metadata_submitted = st.form_submit_button("💾 Save Metadata", type="primary")
            
            if metadata_submitted:
                if question_id and initial_goal and prompt_text and model_combo:
                    detected_language, detected_project_type = parse_question_id(question_id)
                    
                    st.session_state.question_id = question_id
                    st.session_state.initial_goal = initial_goal
                    st.session_state.prompt_text = prompt_text
                    st.session_state.model1 = model_combo[0]
                    st.session_state.model2 = model_combo[1]
                    st.session_state.detected_language = detected_language
                    st.session_state.detected_project_type = detected_project_type
                    st.session_state.metadata_saved = True
                else:
                    st.error("❌ Please complete all required metadata fields")
        
        # Display auto-detected information immediately after form submission
        if metadata_submitted and question_id:
            detected_language, detected_project_type = parse_question_id(question_id)
            
            if detected_language:
                st.success(f"🔍 **Detected Language:** {detected_language}")
            else:
                st.warning("⚠️ Could not detect language from Question ID")
            
            if detected_project_type:
                st.success(f"🔍 **Detected Project Type:** {detected_project_type}")
            else:
                st.warning("⚠️ Could not detect project type from Question ID")
        
        # Show metadata status
        if st.session_state.get('metadata_saved'):
            st.info("✅ Metadata saved - Ready for audio recordings")
        
        # SECTION 2: Audio Recordings Upload
        st.markdown("---")
        st.subheader("🎵 Audio Recordings Upload")
        
        if not st.session_state.get('metadata_saved'):
            st.warning("⚠️ Save metadata first to unlock audio upload")
        else:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"""
                <div class="gemini-section">
                    <h3>🔵 {st.session_state.model1} Audio Recordings</h3>
                    <p>Upload audio recordings generated by {st.session_state.model1}</p>
                </div>
                """, unsafe_allow_html=True)
                
                model1_audio_files = st.file_uploader(
                    f"Upload {st.session_state.model1} audio recordings *",
                    type=['wav', 'mp3', 'm4a', 'flac', 'ogg', 'aac'],
                    accept_multiple_files=True,
                    key="model1_audio_upload",
                    help=f"Upload audio recordings from {st.session_state.model1}"
                )
                
                if model1_audio_files:
                    st.success(f"📁 {len(model1_audio_files)} audio recording(s) uploaded for {st.session_state.model1}")
                    with st.expander("🔍 Preview Files", expanded=True):
                        for i, audio in enumerate(model1_audio_files):
                            st.write(f"• {audio.name} ({audio.size / 1024:.1f} KB)")
                            try:
                                st.audio(audio)
                            except:
                                st.warning(f"Could not preview {audio.name}")
            
            with col2:
                st.markdown(f"""
                <div class="chatgpt-section">
                    <h3>🟢 {st.session_state.model2} Audio Recordings</h3>
                    <p>Upload audio recordings generated by {st.session_state.model2}</p>
                </div>
                """, unsafe_allow_html=True)
                
                model2_audio_files = st.file_uploader(
                    f"Upload {st.session_state.model2} audio recordings *",
                    type=['wav', 'mp3', 'm4a', 'flac', 'ogg', 'aac'],
                    accept_multiple_files=True,
                    key="model2_audio_upload",
                    help=f"Upload audio recordings from {st.session_state.model2}"
                )
                
                if model2_audio_files:
                    st.success(f"📁 {len(model2_audio_files)} audio recording(s) uploaded for {st.session_state.model2}")
                    with st.expander("🔍 Preview Files", expanded=True):
                        for i, audio in enumerate(model2_audio_files):
                            st.write(f"• {audio.name} ({audio.size / 1024:.1f} KB)")
                            try:
                                st.audio(audio)
                            except:
                                st.warning(f"Could not preview {audio.name}")
            
            # Save audio recordings button
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                if st.button("🔊 Save Audio Recordings", type="primary", use_container_width=True):
                    if model1_audio_files and model2_audio_files:
                        st.session_state.model1_audio_files = model1_audio_files
                        st.session_state.model2_audio_files = model2_audio_files
                        st.session_state.audio_saved = True
                        st.balloons()
                    else:
                        st.error("❌ Please upload audio recordings for both models")
        
        # Show audio status
        if st.session_state.get('audio_saved'):
            st.info("✅ Audio recordings saved - Step 1 complete!")
        
        # Show next step button if completed
        show_next_step_button("Metadata & Audio")
    
    elif page == "Audio Verification":
        st.header("2️⃣ Audio Verification")
        
        if not is_step_completed("Metadata & Audio"):
            st.markdown("""
            <div class="error-message">
                <strong>⚠️ Prerequisites Missing:</strong> Please complete Step 1 (Metadata & Audio) first.
            </div>
            """, unsafe_allow_html=True)
            return
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"""
            <div class="info-card">
                <h4>📝 Comparison Information</h4>
                <p><strong>Question ID:</strong> {st.session_state.question_id[:50]}...</p>
                <p><strong>Model Comparison:</strong> {st.session_state.model1} vs {st.session_state.model2}</p>
                <p><strong>Language:</strong> {st.session_state.get('detected_language', 'Not detected')}</p>
                <p><strong>Project Type:</strong> {st.session_state.get('detected_project_type', 'Not detected')}</p>
                <p><strong>Initial Goal:</strong> {st.session_state.initial_goal[:75]}...</p>
                <p><strong>Initial Prompt:</strong> {st.session_state.prompt_text[:75]}...</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="stats-container">
                <div class="stat-card">
                    <h3>{len(st.session_state.model1_audio_files)}</h3>
                    <p>{st.session_state.model1} Files</p>
                </div>
                <div class="stat-card">
                    <h3>{len(st.session_state.model2_audio_files)}</h3>
                    <p>{st.session_state.model2} Files</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Verification button
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("🔄 Verify Audio Recordings", type="primary", use_container_width=True):
                with st.spinner("Verifying audio recordings..."):
                    try:
                        with AudioFileValidator() as audio_validator:
                            verification_results = {
                                'model1': {},
                                'model2': {}
                            }
                            
                            st.write(f"Verifying {st.session_state.model1} audio recordings...")
                            for audio_file in st.session_state.model1_audio_files:
                                result = audio_validator.validate_audio_file(audio_file)
                                transcription_result = audio_validator.placeholder_transcription_validation(
                                    audio_file, st.session_state.get('detected_language')
                                )
                                result['transcription'] = transcription_result
                                verification_results['model1'][audio_file.name] = result
                            
                            st.write(f"Verifying {st.session_state.model2} audio recordings...")
                            for audio_file in st.session_state.model2_audio_files:
                                result = audio_validator.validate_audio_file(audio_file)
                                transcription_result = audio_validator.placeholder_transcription_validation(
                                    audio_file, st.session_state.get('detected_language')
                                )
                                result['transcription'] = transcription_result
                                verification_results['model2'][audio_file.name] = result
                            
                            st.session_state.verification_results = verification_results
                            st.session_state.audio_verification_complete = True
                            
                            st.markdown("""
                            <div class="success-message">
                                <strong>✅ Success!</strong> Audio verification completed! Review the results below.
                            </div>
                            """, unsafe_allow_html=True)
                            st.balloons()
                            
                    except Exception as e:
                        st.markdown(f"""
                        <div class="error-message">
                            <strong>❌ Error:</strong> Failed to verify audio recordings: {str(e)}
                        </div>
                        """, unsafe_allow_html=True)
        
        # Verification Results Display
        if st.session_state.get('audio_verification_complete') and 'verification_results' in st.session_state:
            st.markdown("---")
            st.subheader("📊 Verification Results")
            
            # Model 1 Results
            st.markdown(f"### 🔵 {st.session_state.model1} Results")
            for filename, result in st.session_state.verification_results['model1'].items():
                with st.expander(f"🎵 {filename}", expanded=False):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if result['is_valid']:
                            st.markdown("""
                            <div class="success-message">
                                <strong>✅ Valid Audio Recording</strong>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.markdown("""
                            <div class="error-message">
                                <strong>❌ Invalid Audio Recording</strong>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        st.write(f"**Duration:** {result['duration']:.2f} seconds")
                        st.write(f"**Sample Rate:** {result['sample_rate']} Hz")
                        st.write(f"**Channels:** {result['channels']}")
                        st.write(f"**Format:** {result['format']}")
                    
                    with col2:
                        if result['errors']:
                            st.markdown("**❌ Errors:**")
                            for error in result['errors']:
                                st.write(f"• {error}")
                        
                        if result['warnings']:
                            st.markdown("**⚠️ Warnings:**")
                            for warning in result['warnings']:
                                st.write(f"• {warning}")
            
            # Model 2 Results
            st.markdown(f"### 🟢 {st.session_state.model2} Results")
            for filename, result in st.session_state.verification_results['model2'].items():
                with st.expander(f"🎵 {filename}", expanded=False):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if result['is_valid']:
                            st.markdown("""
                            <div class="success-message">
                                <strong>✅ Valid Audio Recording</strong>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.markdown("""
                            <div class="error-message">
                                <strong>❌ Invalid Audio Recording</strong>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        st.write(f"**Duration:** {result['duration']:.2f} seconds")
                        st.write(f"**Sample Rate:** {result['sample_rate']} Hz")
                        st.write(f"**Channels:** {result['channels']}")
                        st.write(f"**Format:** {result['format']}")
                    
                    with col2:
                        if result['errors']:
                            st.markdown("**❌ Errors:**")
                            for error in result['errors']:
                                st.write(f"• {error}")
                        
                        if result['warnings']:
                            st.markdown("**⚠️ Warnings:**")
                            for warning in result['warnings']:
                                st.write(f"• {warning}")
            
            # Transcription placeholder info
            st.markdown("""
            <div class="warning-message">
                <strong>🔄 Transcription Validation:</strong> Placeholder implementation ready for future integration with ASR services for side-by-side transcription comparison.
            </div>
            """, unsafe_allow_html=True)
        
        # Show next step button if completed
        show_next_step_button("Audio Verification")
    
    elif page == "Summary & Submission":
        st.header("3️⃣ Summary & Submission")
        
        if not st.session_state.get('audio_verification_complete'):
            st.markdown("""
            <div class="error-message">
                <strong>⚠️ Prerequisites Missing:</strong> Please complete Step 2 (Audio Verification) first.
            </div>
            """, unsafe_allow_html=True)
            return
        
        # Calculate verification statistics
        model1_files = len(st.session_state.model1_audio_files)
        model2_files = len(st.session_state.model2_audio_files)
        
        model1_valid = sum(1 for result in st.session_state.verification_results['model1'].values() 
                          if result.get('is_valid', False))
        model2_valid = sum(1 for result in st.session_state.verification_results['model2'].values() 
                          if result.get('is_valid', False))
        
        model1_duration = sum(result.get('duration', 0) for result in st.session_state.verification_results['model1'].values())
        model2_duration = sum(result.get('duration', 0) for result in st.session_state.verification_results['model2'].values())
        
        # Custom Form Container
        st.markdown("""
        <div class="custom-form-container">
            <h3 style="text-align: center; margin-bottom: 0.1rem; color: #e3f2fd;">
                📋 Audio Evaluation Submission Form
            </h3>
        """, unsafe_allow_html=True)
        
        # Create form using columns to simulate the custom form layout
        
        # Email Input Row
        col1, col2, col3 = st.columns([2, 6, 2])
        with col1:
            st.markdown('<p class="form-label">Email Address:</p>', unsafe_allow_html=True)
        with col2:
            user_email = st.text_input(
                "",
                placeholder="Please input your evaluation alias email",
                key="email_input",
                label_visibility="collapsed"
            )
        with col3:
            if user_email:
                if validate_email_format(user_email):
                    # PLACEHOLDER: Email validation against spreadsheet
                    is_email_valid = validate_email_against_spreadsheet(user_email)
                    if is_email_valid:
                        st.markdown('<div class="validation-status validation-success">✓ Valid</div>', unsafe_allow_html=True)
                        st.session_state.email_validated = True
                    else:
                        st.markdown('<div class="validation-status validation-error">✗ Not Found</div>', unsafe_allow_html=True)
                        st.session_state.email_validated = False
                else:
                    st.markdown('<div class="validation-status validation-error">✗ Invalid Format</div>', unsafe_allow_html=True)
                    st.session_state.email_validated = False
            else:
                st.markdown('<div class="validation-status">⚪ Pending</div>', unsafe_allow_html=True)
                st.session_state.email_validated = False
        
        st.markdown('<hr style="margin: 1rem 0; border: 1px solid rgba(255,255,255,0.1);">', unsafe_allow_html=True)
        
        # Question ID Row
        col1, col2, col3 = st.columns([2, 8, 2])
        with col1:
            st.markdown('<p class="form-label">Question ID:</p>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'<div class="form-value readonly">{st.session_state.question_id}</div>', unsafe_allow_html=True)
        
        st.markdown('<hr style="margin: 1rem 0; border: 1px solid rgba(255,255,255,0.1);">', unsafe_allow_html=True)
        
        # Initial Goal Row
        col1, col2, col3 = st.columns([2, 6, 2])
        with col1:
            st.markdown('<p class="form-label">Initial Goal:</p>', unsafe_allow_html=True)
        with col2:
            goal_display = st.session_state.initial_goal[:100] + "..." if len(st.session_state.initial_goal) > 100 else st.session_state.initial_goal
            st.markdown(f'<div class="form-value readonly">{goal_display}</div>', unsafe_allow_html=True)
        with col3:
            detected_language = st.session_state.get('detected_language')
            if detected_language:
                st.markdown(f'<div class="validation-status validation-success">🌐 {detected_language}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="validation-status">🌐 Not Detected</div>', unsafe_allow_html=True)
        
        st.markdown('<hr style="margin: 1rem 0; border: 1px solid rgba(255,255,255,0.1);">', unsafe_allow_html=True)
        
        # Prompt Text Row
        col1, col2, col3 = st.columns([2, 6, 2])
        with col1:
            st.markdown('<p class="form-label">Prompt Text:</p>', unsafe_allow_html=True)
        with col2:
            prompt_display = st.session_state.prompt_text[:100] + "..." if len(st.session_state.prompt_text) > 100 else st.session_state.prompt_text
            st.markdown(f'<div class="form-value readonly">{prompt_display}</div>', unsafe_allow_html=True)
        with col3:
            detected_project = st.session_state.get('detected_project_type')
            if detected_project:
                st.markdown(f'<div class="validation-status validation-success">📂 {detected_project}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="validation-status">📂 Not Detected</div>', unsafe_allow_html=True)
        
        st.markdown('<hr style="margin: 1rem 0; border: 1px solid rgba(255,255,255,0.1);">', unsafe_allow_html=True)
        
        # Model 1 Row
        col1, col2, col3 = st.columns([2, 8, 2])
        with col1:
            st.markdown('<p class="form-label">Model 1:</p>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'''
            <div class="audio-info">
                <span class="audio-icon">🔵</span>
                <div>
                    <strong>{st.session_state.model1}</strong><br>
                    <small>{model1_files} audio file(s) | {model1_valid} valid | {model1_duration:.1f}s total</small>
                </div>
            </div>
            ''', unsafe_allow_html=True)
        
        st.markdown('<hr style="margin: 1rem 0; border: 1px solid rgba(255,255,255,0.1);">', unsafe_allow_html=True)
        
        # Model 2 Row
        col1, col2, col3 = st.columns([2, 8, 2])
        with col1:
            st.markdown('<p class="form-label">Model 2:</p>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'''
            <div class="audio-info">
                <span class="audio-icon">🟢</span>
                <div>
                    <strong>{st.session_state.model2}</strong><br>
                    <small>{model2_files} audio file(s) | {model2_valid} valid | {model2_duration:.1f}s total</small>
                </div>
            </div>
            ''', unsafe_allow_html=True)
        
        st.markdown('<hr style="margin: 1rem 0; border: 1px solid rgba(255,255,255,0.1);">', unsafe_allow_html=True)
        
        # Audio Validation Results and Drive URL Row
        col1, col2, col3 = st.columns([2, 6, 2])
        with col1:
            st.markdown('<p class="form-label">Validation Results:</p>', unsafe_allow_html=True)
        with col2:
            # Generate filename for the results package
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"SxS_Audio_Evaluation_{st.session_state.model1}_vs_{st.session_state.model2}_{timestamp}"
            total_files = model1_files + model2_files
            total_valid = model1_valid + model2_valid
            total_duration = model1_duration + model2_duration
            
            st.markdown(f'''
            <div class="audio-info">
                <span class="audio-icon">🎵</span>
                <div>
                    <strong>Audio Package: {filename}.zip</strong><br>
                    <small>{total_files} files | {total_valid} valid | {total_duration:.1f}s duration</small>
                </div>
            </div>
            ''', unsafe_allow_html=True)
        with col3:
            # Load Button for Drive URL
            load_button_disabled = not st.session_state.email_validated
            if st.button("Load", key="load_drive_url", disabled=load_button_disabled):
                with st.spinner("Uploading to Drive..."):
                    # PLACEHOLDER: Generate Drive URL
                    metadata = {
                        'user_email': user_email,
                        'question_id': st.session_state.question_id,
                        'model1': st.session_state.model1,
                        'model2': st.session_state.model2,
                        'timestamp': datetime.now().isoformat(),
                        'validation_results': st.session_state.verification_results
                    }
                    
                    # Create package of audio files and validation results
                    audio_package = {
                        'model1_files': st.session_state.model1_audio_files,
                        'model2_files': st.session_state.model2_audio_files,
                        'validation_results': st.session_state.verification_results,
                        'metadata': metadata
                    }
                    
                    drive_url = generate_drive_url_placeholder(audio_package, filename, metadata)
                    st.session_state.drive_url = drive_url
                    st.session_state.drive_url_generated = True
                    st.success("Drive URL generated successfully!")
                    st.rerun()
        
        # Drive URL Display Row
        col1, col2, col3 = st.columns([2, 8, 2])
        with col1:
            st.markdown('<p class="form-label">Drive URL:</p>', unsafe_allow_html=True)
        with col2:
            if st.session_state.drive_url_generated and st.session_state.drive_url:
                st.markdown(f'<div class="drive-url-display drive-url-ready">{st.session_state.drive_url}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="drive-url-display">URL will be generated after clicking Load...</div>', unsafe_allow_html=True)
        
        st.markdown('<hr style="margin: 2rem 0; border: 1px solid rgba(255,255,255,0.1);">', unsafe_allow_html=True)
        
        # Submit Button Row
        col1, col2, col3 = st.columns([4, 4, 4])
        with col2:
            submit_disabled = not (st.session_state.email_validated and st.session_state.drive_url_generated)
            
            if st.button("📤 Submit Evaluation", key="submit_form", disabled=submit_disabled, use_container_width=True):
                with st.spinner("Submitting evaluation results..."):
                    # PLACEHOLDER: Submit to spreadsheet
                    form_data = {
                        'timestamp': datetime.now().isoformat(),
                        'user_email': user_email,
                        'question_id': st.session_state.question_id,
                        'initial_goal': st.session_state.initial_goal,
                        'prompt_text': st.session_state.prompt_text,
                        'detected_language': st.session_state.get('detected_language'),
                        'detected_project_type': st.session_state.get('detected_project_type'),
                        'model1': st.session_state.model1,
                        'model2': st.session_state.model2,
                        'model1_files_count': model1_files,
                        'model2_files_count': model2_files,
                        'model1_valid_count': model1_valid,
                        'model2_valid_count': model2_valid,
                        'model1_duration': model1_duration,
                        'model2_duration': model2_duration,
                        'total_files': total_files,
                        'total_valid': total_valid,
                        'total_duration': total_duration,
                        'validation_results': st.session_state.verification_results,
                        'drive_url': st.session_state.drive_url,
                        'package_filename': filename
                    }
                    
                    success = submit_to_spreadsheet_placeholder(form_data)
                    
                    if success:
                        st.session_state.submission_complete = True
                        st.success("🎉 Evaluation submitted successfully!")
                        st.balloons()
                        
                        # Display success message
                        st.markdown(f"""
                        <div class="success-message">
                            <h4>✅ Submission Completed!</h4>
                            <p><strong>Email:</strong> {user_email}</p>
                            <p><strong>Package:</strong> {filename}.zip</p>
                            <p><strong>Drive URL:</strong> <a href="{st.session_state.drive_url}" target="_blank">View Results</a></p>
                            <p><strong>Timestamp:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.error("❌ Submission failed. Please try again.")
            
            # Show submission requirements
            if submit_disabled:
                requirements = []
                if not st.session_state.email_validated:
                    requirements.append("✗ Valid email required")
                if not st.session_state.drive_url_generated:
                    requirements.append("✗ Drive URL required (click Load)")
                
                st.markdown(f'<div style="text-align: center; color: #ffa726; font-size: 0.9rem; margin-top: 1rem;">{"<br>".join(requirements)}</div>', unsafe_allow_html=True)
        
        # Close the custom form container
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Add spacing after the form
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Completion actions
        if st.session_state.get('submission_complete'):
            st.markdown("---")
            st.subheader("🎉 Evaluation Complete")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.success("✅ Results successfully submitted to tracking system!")
                st.info(f"📧 **Confirmation sent to:** {user_email}")
                if st.session_state.drive_url:
                    st.info(f"🔗 **Drive URL:** [View Results]({st.session_state.drive_url})")
            
            with col2:
                if st.button("🔄 Start New Evaluation", type="primary"):
                    # Clear session state but keep navigation page
                    keys_to_clear = [key for key in st.session_state.keys() if key != 'current_page']
                    for key in keys_to_clear:
                        del st.session_state[key]
                    
                    # Reset to first step
                    st.session_state.current_page = "Metadata & Audio"
                    
                    # Reinitialize state variables
                    st.session_state.metadata_saved = False
                    st.session_state.audio_saved = False
                    st.session_state.email_validated = False
                    st.session_state.drive_url_generated = False
                    st.session_state.drive_url = ""
                    st.session_state.user_email = ""
                    st.session_state.audio_verification_complete = False
                    st.session_state.submission_complete = False
                    
                    st.success("🆕 Ready for a new evaluation!")
                    st.rerun()
    
    elif page == "Help":
        st.header("❓ Help & Documentation")
        
        tab1, tab2, tab3 = st.tabs(["📋 Instructions", "🔧 Troubleshooting", "📊 Examples"])
        
        with tab1:
            st.markdown("""
            ### 📋 How to Use This App
            
            #### 1️⃣ Metadata & Audio Recordings
            - **Step 1a:** Enter the **Question ID**, select **Model Combination**, enter **Initial Goal** and **Initial Prompt**
            - **Click "Save Metadata"** to store basic information and unlock audio upload
            - **Step 1b:** Upload **audio recordings for each model** separately with immediate preview
            - **Click "Save Audio Recordings"** to store audio files and complete Step 1
            - Review **auto-detected language and project type** from Question ID
            
            #### 2️⃣ Audio Verification
            - Review metadata and file counts from Step 1
            - Click **Verify Audio Recordings** to run comprehensive validation
            - Review validation results for both models including:
              - Audio corruption detection
              - Duration validation (minimum 1 minute recommended)
              - Format and technical specifications
              - Placeholder for future transcription comparison
            
            #### 3️⃣ Summary & Submission
            - Review complete **evaluation summary** with statistics
            - Enter your **email address** for submission tracking
            - Generate **Drive URL** for results storage
            - **Submit evaluation results** to tracking system
            
            ### 🎵 Supported Audio Formats
            - WAV, MP3, M4A, FLAC, OGG, AAC
            - Maximum file size: 200MB per file
            - Minimum duration: 1 second (1 minute recommended)
            
            ### 🔍 Validation Checks
            - **Corruption Detection**: Verifies file integrity
            - **Playability**: Confirms audio can be loaded and processed
            - **Duration**: Checks minimum length requirements
            - **Format**: Validates audio specifications
            - **SxS Comparison**: Side-by-side validation of both models
            """)
        
        with tab2:
            st.markdown("""
            ### 🔧 Troubleshooting
            
            #### Common Issues:
            - **Question ID parsing fails**: Ensure ID follows expected format with language and project type
            - **Audio validation errors**: Check file format and ensure files are not corrupted
            - **Email not validated**: Verify email format and authorization status
            - **Upload failures**: Ensure files are under size limit and in supported formats
            - **Drive URL generation fails**: Complete email validation first
            - **Navigation disabled**: Complete current step before proceeding to next
            
            #### Best Practices:
            - **Complete metadata first** - Save metadata before uploading audio recordings
            - Use high-quality audio recordings with clear speech
            - Ensure both models received the same prompt
            - Upload audio recordings in consistent format for fair comparison
            - Test with a single file pair first before batch processing
            - Keep original audio recordings as backup before validation
            
            #### SxS Evaluation Tips:
            - Ensure both models were given identical prompts
            - Use consistent audio quality and format for both models
            - Upload files in logical order for easy comparison
            - Review validation results to ensure fair comparison conditions
            
            #### Regex Patterns Used:
            - **Language Detection**: `human_eval_([a-z]{2}-[A-Z]{2}|[a-z]{2}-\\d{3}|[a-z]{2}-[a-z]{2})\\+INTERNAL`
              - Supports: uppercase (zh-CN), numeric (es-419), and lowercase (es-en) patterns
            - **Project Type Detection**: `experience_([a-z_]+)_human_eval`
            """)
        
        with tab3:
            st.markdown("""
            ### 📊 Examples
            
            #### Sample Question IDs:
            ```
            30aeeee4a88e5dd6e04a0c5fd0400b4a+bard_data+coach_P128214_quality_gemini_live_sxs_e2e_experience_monolingual_human_eval_zh-CN+INTERNAL+en:4938557666299164772
            ```
            **Detected:** Language=zh-CN, Project=Monolingual
            
            ```
            deca6778ec3c6732889541e47526462c+bard_data+coach_P128239_quality_gemini_live_sxs_e2e_experience_audio_out_human_eval_de-DE+INTERNAL+en:5086465366914833277
            ```
            **Detected:** Language=de-DE, Project=Audio Out
            
            ```
            ee237a0a92ecf99df4fa773ec17ef8c8+bard_data+coach_P128260_quality_gemini_live_sxs_e2e_experience_code_mixed_human_eval_es-en+INTERNAL+en:16950462059114391870
            ```
            **Detected:** Language=es-en, Project=Mixed
            
            #### Supported Languages:
            id-ID, ar-EG, ko-KR, es-419, pt-BR, hi-IN, en-IN, ja-JP, hi-EN, ko-EN, id-EN, vi-VN, pt-EN, de-DE, fr-FR, zh-CN, nl-NL, ru-EN, ja-KR, es-EN, zh-TW, ar-EN, zh-EN, fr-EN, ja-EN, de-EN, ko-JA, ko-ZH, **es-en** (lowercase-lowercase pattern)
            
            #### Project Types:
            - **Monolingual**: Single language audio content
            - **Audio Out**: Text-to-speech evaluation
            - **Mixed**: Code-mixed or multilingual content
            - **Language Learning**: Educational language content
            
            #### Model Combinations:
            - **Gemini vs ChatGPT**: Standard comparison setup
            - **ChatGPT vs Gemini**: Alternative order for testing
            
            #### SxS Evaluation Workflow:
            1. Parse Question ID → Extract metadata + Upload audio recordings
            2. Run verification → Technical analysis of both models
            3. Review results → Side-by-side comparison
            4. Submit → Track in evaluation system
            """)

if __name__ == "__main__":
    main()