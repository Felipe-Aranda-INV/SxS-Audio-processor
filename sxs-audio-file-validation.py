import streamlit as st
import io
import re
import wave
import librosa
import soundfile as sf
from datetime import datetime
import tempfile
import os
import traceback
from typing import List, Optional, Tuple, Dict, Any
import time

# Configure page
st.set_page_config(
    page_title="Audio File Validation System",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for consistent styling with original app
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
    
    .audio-info-card {
        background-color: #fff8e1;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        border-left: 4px solid #ff9800;
        color: #e65100;
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
    
    .navigation-tip {
        background-color: #ffecd2;
        color: #856404;
        padding: 0.8rem;
        border-radius: 5px;
        margin: 1rem 0;
        border: 1px solid #ffeaa7;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

# Constants for validation
ALLOWED_LANGUAGES = [
    "id-ID", "ar-EG", "ko-KR", "es-419", "pt-BR", "hi-IN", "en-IN", "ja-JP",
    "hi-EN", "ko-EN", "id-EN", "vi-VN", "pt-EN", "de-DE", "fr-FR", "zh-CN",
    "nl-NL", "ru-EN", "ja-KR", "es-EN", "zh-TW", "ar-EN", "zh-EN", "fr-EN",
    "ja-EN", "de-EN", "ko-JA", "ko-ZH"
]

PROJECT_TYPES = ["Monolingual", "Audio Out", "Mixed", "Language Learning"]

MODEL_OPTIONS = ["Gemini", "ChatGPT"]

# Minimum audio duration in seconds (1 minute)
MIN_AUDIO_DURATION = 60.0

class AudioFileValidator:
    """
    Production-grade audio file validator with comprehensive validation capabilities.
    
    This class handles:
    - Audio file corruption detection
    - Audio readability verification
    - Duration validation
    - Format validation
    - Placeholder for future transcription validation
    """
    
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
        """
        Comprehensive audio file validation.
        
        Returns:
            Dict containing validation results with keys:
            - is_valid: bool
            - duration: float (seconds)
            - sample_rate: int
            - channels: int
            - format: str
            - errors: List[str]
            - warnings: List[str]
        """
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
            # Reset file pointer
            audio_file.seek(0)
            
            # Create temporary file for processing
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f"_{audio_file.name}")
            temp_file.write(audio_file.read())
            temp_file.close()
            
            self.temp_files.append(temp_file.name)
            
            # Basic file existence and size check
            if not os.path.exists(temp_file.name) or os.path.getsize(temp_file.name) == 0:
                result['errors'].append("Audio file is empty or corrupted")
                return result
            
            # Attempt to load audio file using librosa for comprehensive analysis
            try:
                audio_data, sample_rate = librosa.load(temp_file.name, sr=None)
                duration = len(audio_data) / sample_rate
                
                result['duration'] = duration
                result['sample_rate'] = sample_rate
                result['format'] = os.path.splitext(audio_file.name)[1].lower()
                
                # Check for corruption by analyzing audio data
                if len(audio_data) == 0:
                    result['errors'].append("Audio file contains no readable audio data")
                    return result
                
                # Check for extremely short duration
                if duration < 1.0:
                    result['errors'].append("Audio duration is less than 1 second")
                    return result
                
                # Check minimum duration requirement
                if duration < MIN_AUDIO_DURATION:
                    result['warnings'].append(f"Audio duration ({duration:.1f}s) is below recommended minimum ({MIN_AUDIO_DURATION}s)")
                
                # Additional validation using soundfile for format verification
                try:
                    with sf.SoundFile(temp_file.name) as f:
                        result['channels'] = f.channels
                        
                        # Verify we can read some data
                        test_frames = f.read(1024)
                        if len(test_frames) == 0:
                            result['errors'].append("Cannot read audio frames from file")
                            return result
                            
                except Exception as sf_error:
                    result['warnings'].append(f"Secondary format validation warning: {str(sf_error)}")
                
                # If we reach here, basic validation passed
                result['is_valid'] = True
                
            except Exception as librosa_error:
                result['errors'].append(f"Audio loading failed: {str(librosa_error)}")
                
                # Fallback: try with wave module for basic WAV files
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
    
    def placeholder_transcription_validation(self, audio_file) -> Dict[str, Any]:
        """
        PLACEHOLDER: Future transcription validation functionality.
        
        This function will be implemented to:
        1. Perform automated speech recognition (ASR) on the audio file
        2. Validate transcription quality and accuracy
        3. Check for language consistency with metadata
        4. Detect audio quality issues affecting transcription
        
        Args:
            audio_file: Audio file to transcribe and validate
            
        Returns:
            Dict containing transcription validation results
        """
        placeholder_result = {
            'transcription_available': False,
            'transcription_text': '',
            'language_detected': '',
            'confidence_score': 0.0,
            'quality_metrics': {
                'clarity_score': 0.0,
                'noise_level': 0.0,
                'speech_to_noise_ratio': 0.0
            },
            'validation_status': 'PLACEHOLDER_NOT_IMPLEMENTED'
        }
        
        # TODO: Implement actual transcription validation
        # This will integrate with:
        # - Google Speech-to-Text API
        # - Azure Cognitive Services Speech
        # - OpenAI Whisper
        # - Custom ASR models
        
        return placeholder_result

def parse_question_id(question_id: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Parse Question ID to extract language and project type using regex patterns.
    
    Args:
        question_id: The question ID string to parse
        
    Returns:
        Tuple of (language, project_type) or (None, None) if parsing fails
    """
    language = None
    project_type = None
    
    try:
        # Extract language pattern: human_eval_[LANGUAGE]+INTERNAL
        # Matches patterns like: human_eval_zh-CN+INTERNAL, human_eval_es-419+INTERNAL
        language_pattern = r'human_eval_([a-z]{2}-[A-Z]{2}|[a-z]{2}-\d{3})\+INTERNAL'
        language_match = re.search(language_pattern, question_id)
        
        if language_match:
            extracted_lang = language_match.group(1)
            if extracted_lang in ALLOWED_LANGUAGES:
                language = extracted_lang
        
        # Extract project type from the experience section
        # Maps internal names to display names
        project_type_mapping = {
            'monolingual': 'Monolingual',
            'audio_out': 'Audio Out',
            'mixed': 'Mixed',
            'code_mixed': 'Mixed',  # Alternative pattern for mixed
            'language_learning': 'Language Learning'
        }
        
        # Pattern to match project type in the question ID
        project_pattern = r'experience_([a-z_]+)_human_eval'
        project_match = re.search(project_pattern, question_id)
        
        if project_match:
            extracted_project = project_match.group(1)
            # Check for direct matches or partial matches
            for key, value in project_type_mapping.items():
                if key in extracted_project:
                    project_type = value
                    break
        
    except Exception as e:
        st.warning(f"Error parsing Question ID: {e}")
    
    return language, project_type

def get_step_status(current_page: str) -> List[str]:
    """Get the status of each step based on session state"""
    steps = ["1️⃣ Metadata Input", "2️⃣ Audio Verification", "3️⃣ Summary & Submission"]
    statuses = []
    
    for i, step in enumerate(steps):
        if step.endswith(current_page):
            statuses.append("active")
        else:
            # Check completion status
            if step.endswith("Metadata Input") and is_step_completed("Metadata Input"):
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
    steps = ["1️⃣ Metadata Input", "2️⃣ Audio Verification", "3️⃣ Summary & Submission"]
    
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
    if step_name == "Metadata Input":
        required_keys = ['question_id', 'selected_model', 'initial_goal', 'initial_prompt', 'audio_files']
        return all(key in st.session_state and st.session_state[key] for key in required_keys)
    elif step_name == "Audio Verification":
        return ('audio_validation_results' in st.session_state and 
                st.session_state.audio_validation_results and
                st.session_state.get('audio_verification_complete', False))
    elif step_name == "Summary & Submission":
        return st.session_state.get('submission_complete', False)
    return False

def get_next_step(current_page: str) -> Optional[str]:
    """Get the next step in the workflow"""
    steps = ["Metadata Input", "Audio Verification", "Summary & Submission"]
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
    """
    PLACEHOLDER: Email validation against authorized users spreadsheet.
    
    This function will be implemented to:
    1. Connect to Google Sheets or other data source
    2. Validate email against authorized users list
    3. Return authentication status
    
    Args:
        email: Email address to validate
        
    Returns:
        bool: True if email is authorized, False otherwise
    """
    # Placeholder validation for demo purposes
    return "@" in email and any(email.endswith(domain) for domain in [".com", ".org", ".net", ".edu"])

def submit_validation_results(form_data: Dict[str, Any]) -> bool:
    """
    PLACEHOLDER: Submit validation results to tracking system.
    
    This function will be implemented to:
    1. Format validation results for storage
    2. Upload to Google Drive or cloud storage
    3. Log to tracking spreadsheet
    4. Send notification emails if required
    
    Args:
        form_data: Complete validation results and metadata
        
    Returns:
        bool: True if submission successful, False otherwise
    """
    # Placeholder success for demo purposes
    return True

def main():
    # Initialize current page in session state
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "Metadata Input"
    
    # Initialize validation state variables
    if 'email_validated' not in st.session_state:
        st.session_state.email_validated = False
    if 'audio_verification_complete' not in st.session_state:
        st.session_state.audio_verification_complete = False
    if 'submission_complete' not in st.session_state:
        st.session_state.submission_complete = False
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🎵 Audio File Validation System</h1>
        <p>Comprehensive audio file validation for LLM evaluation datasets</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar navigation
    st.sidebar.title("🧭 Navigation")
    
    nav_options = [
        "1️⃣ Metadata Input",
        "2️⃣ Audio Verification", 
        "3️⃣ Summary & Submission",
        "❓ Help"
    ]
    
    page_mapping = {
        "1️⃣ Metadata Input": "Metadata Input",
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
        current_nav_selection = "1️⃣ Metadata Input"
    
    # Display navigation with status
    selected_nav = st.sidebar.radio(
        "Choose Step:",
        nav_options,
        index=nav_options.index(current_nav_selection) if current_nav_selection in nav_options else 0,
        format_func=lambda x: f"{x} {'✅' if is_step_completed(page_mapping[x]) else ''}"
    )
    
    # Update session state based on selection
    page = page_mapping[selected_nav]
    st.session_state.current_page = page
    
    # Navigation tips
    st.sidebar.markdown("""
    <div class="navigation-tip">
        💡 <strong>Navigation Tip:</strong><br>
        Complete each step to unlock the next one. Look for the "Continue" button at the bottom of each completed step!
    </div>
    """, unsafe_allow_html=True)
    
    # Session info in sidebar
    if 'question_id' in st.session_state:
        st.sidebar.markdown("### 📋 Current Session")
        st.sidebar.info(f"**ID:** {st.session_state.question_id[:20]}...")
        if 'selected_model' in st.session_state:
            st.sidebar.info(f"**Model:** {st.session_state.selected_model}")
        if 'detected_language' in st.session_state and st.session_state.detected_language:
            st.sidebar.info(f"**Language:** {st.session_state.detected_language}")
        if 'detected_project_type' in st.session_state and st.session_state.detected_project_type:
            st.sidebar.info(f"**Project:** {st.session_state.detected_project_type}")
    
    # Session stats
    if 'audio_files' in st.session_state and st.session_state.audio_files:
        st.sidebar.markdown("### 📊 Session Stats")
        st.sidebar.metric("Audio Files", len(st.session_state.audio_files))
        if 'audio_validation_results' in st.session_state:
            valid_count = sum(1 for result in st.session_state.audio_validation_results.values() if result.get('is_valid', False))
            st.sidebar.metric("Valid Files", f"{valid_count}/{len(st.session_state.audio_files)}")
    
    # Display step indicator
    display_step_indicator(page)
    
    # Page content
    if page == "Metadata Input":
        st.header("1️⃣ Metadata Input")
        
        st.markdown("""
        <div class="info-card">
            <h4>📋 Required Information</h4>
            <p>Please provide the basic information for your audio validation. All fields marked with * are required.</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("metadata_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                question_id = st.text_input(
                    "Question ID *",
                    placeholder="e.g., 30aeeee4a88e5dd6e04a0c5fd0400b4a+bard_data+coach_P128214...",
                    help="Enter the unique identifier for this validation task",
                    value=st.session_state.get('question_id', '')
                )
                
                selected_model = st.selectbox(
                    "Model Selection *",
                    options=MODEL_OPTIONS,
                    help="Choose the model being evaluated",
                    index=MODEL_OPTIONS.index(st.session_state.get('selected_model', MODEL_OPTIONS[0])) if st.session_state.get('selected_model') in MODEL_OPTIONS else 0
                )
                
                # Display auto-detected information
                if question_id:
                    detected_language, detected_project_type = parse_question_id(question_id)
                    
                    if detected_language:
                        st.success(f"🔍 **Detected Language:** {detected_language}")
                    else:
                        st.warning("⚠️ Could not detect language from Question ID")
                    
                    if detected_project_type:
                        st.success(f"🔍 **Detected Project Type:** {detected_project_type}")
                    else:
                        st.warning("⚠️ Could not detect project type from Question ID")
            
            with col2:
                initial_goal = st.text_area(
                    "Initial Goal *",
                    placeholder="Describe the goal of this evaluation task...",
                    height=100,
                    help="The main objective of this audio evaluation",
                    value=st.session_state.get('initial_goal', '')
                )
                
                initial_prompt = st.text_area(
                    "Initial Prompt *",
                    placeholder="Enter the prompt that was used to generate the audio...",
                    height=100,
                    help="The prompt that was given to the model",
                    value=st.session_state.get('initial_prompt', '')
                )
            
            # Audio files upload section
            st.markdown("""
            <div class="upload-section">
                <h3>🎵 Audio Files Upload</h3>
                <p>Upload audio files for validation (supports multiple files)</p>
            </div>
            """, unsafe_allow_html=True)
            
            audio_files = st.file_uploader(
                "Upload Audio Files *",
                type=['wav', 'mp3', 'm4a', 'flac', 'ogg', 'aac'],
                accept_multiple_files=True,
                help="Upload audio files for validation"
            )
            
            if audio_files:
                st.success(f"📁 {len(audio_files)} audio file(s) uploaded")
                for i, audio_file in enumerate(audio_files):
                    st.write(f"• {audio_file.name} ({audio_file.size / 1024:.1f} KB)")
            
            submitted = st.form_submit_button("💾 Save Metadata", type="primary")
            
            if submitted:
                if question_id and selected_model and initial_goal and initial_prompt and audio_files:
                    # Parse the question ID
                    detected_language, detected_project_type = parse_question_id(question_id)
                    
                    # Store in session state
                    st.session_state.question_id = question_id
                    st.session_state.selected_model = selected_model
                    st.session_state.initial_goal = initial_goal
                    st.session_state.initial_prompt = initial_prompt
                    st.session_state.audio_files = audio_files
                    st.session_state.detected_language = detected_language
                    st.session_state.detected_project_type = detected_project_type
                    
                    st.markdown("""
                    <div class="success-message">
                        <strong>✅ Success!</strong> Metadata saved successfully! You can now proceed to Step 2.
                    </div>
                    """, unsafe_allow_html=True)
                    st.balloons()
                else:
                    st.markdown("""
                    <div class="error-message">
                        <strong>❌ Error:</strong> Please fill in all required fields marked with *.
                    </div>
                    """, unsafe_allow_html=True)
        
        # Show next step button if completed
        show_next_step_button("Metadata Input")
    
    elif page == "Audio Verification":
        st.header("2️⃣ Audio Verification")
        
        if not is_step_completed("Metadata Input"):
            st.markdown("""
            <div class="error-message">
                <strong>⚠️ Prerequisites Missing:</strong> Please complete Step 1 (Metadata Input) first.
            </div>
            """, unsafe_allow_html=True)
            return
        
        st.markdown(f"""
        <div class="info-card">
            <h4>📋 Current Session</h4>
            <p><strong>Model:</strong> {st.session_state.selected_model}</p>
            <p><strong>Language:</strong> {st.session_state.get('detected_language', 'Not detected')}</p>
            <p><strong>Project Type:</strong> {st.session_state.get('detected_project_type', 'Not detected')}</p>
            <p><strong>Audio Files:</strong> {len(st.session_state.audio_files)} file(s)</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Audio validation section
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("🔍 Validate Audio Files", type="primary", use_container_width=True):
                with st.spinner("Validating audio files..."):
                    try:
                        with AudioFileValidator() as validator:
                            validation_results = {}
                            
                            for i, audio_file in enumerate(st.session_state.audio_files):
                                st.write(f"Validating: {audio_file.name}")
                                
                                # Validate audio file
                                result = validator.validate_audio_file(audio_file)
                                validation_results[audio_file.name] = result
                                
                                # Get transcription validation placeholder
                                transcription_result = validator.placeholder_transcription_validation(audio_file)
                                validation_results[audio_file.name]['transcription'] = transcription_result
                            
                            # Store results in session state
                            st.session_state.audio_validation_results = validation_results
                            st.session_state.audio_verification_complete = True
                            
                            st.markdown("""
                            <div class="success-message">
                                <strong>✅ Success!</strong> Audio validation completed! Review results below.
                            </div>
                            """, unsafe_allow_html=True)
                            st.balloons()
                            
                    except Exception as e:
                        st.markdown(f"""
                        <div class="error-message">
                            <strong>❌ Error:</strong> Audio validation failed: {str(e)}
                        </div>
                        """, unsafe_allow_html=True)
        
        # Display validation results
        if st.session_state.get('audio_verification_complete') and 'audio_validation_results' in st.session_state:
            st.markdown("---")
            st.subheader("📊 Validation Results")
            
            for filename, result in st.session_state.audio_validation_results.items():
                with st.expander(f"🎵 {filename}", expanded=True):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if result['is_valid']:
                            st.markdown("""
                            <div class="success-message">
                                <strong>✅ Valid Audio File</strong>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.markdown("""
                            <div class="error-message">
                                <strong>❌ Invalid Audio File</strong>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        # Display audio information
                        st.write(f"**Duration:** {result['duration']:.2f} seconds")
                        st.write(f"**Sample Rate:** {result['sample_rate']} Hz")
                        st.write(f"**Channels:** {result['channels']}")
                        st.write(f"**Format:** {result['format']}")
                    
                    with col2:
                        # Display errors
                        if result['errors']:
                            st.markdown("**❌ Errors:**")
                            for error in result['errors']:
                                st.write(f"• {error}")
                        
                        # Display warnings
                        if result['warnings']:
                            st.markdown("**⚠️ Warnings:**")
                            for warning in result['warnings']:
                                st.write(f"• {warning}")
                    
                    # Transcription placeholder info
                    if 'transcription' in result:
                        st.markdown("""
                        <div class="warning-message">
                            <strong>🔄 Transcription Validation:</strong> Placeholder implementation ready for future integration with ASR services.
                        </div>
                        """, unsafe_allow_html=True)
        
        # Show next step button if completed
        show_next_step_button("Audio Verification")
    
    elif page == "Summary & Submission":
        st.header("3️⃣ Summary & Submission")
        
        if not is_step_completed("Audio Verification"):
            st.markdown("""
            <div class="error-message">
                <strong>⚠️ Prerequisites Missing:</strong> Please complete Step 2 (Audio Verification) first.
            </div>
            """, unsafe_allow_html=True)
            return
        
        # Summary section
        st.subheader("📋 Validation Summary")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"""
            <div class="info-card">
                <h4>📝 Session Metadata</h4>
                <p><strong>Question ID:</strong> {st.session_state.question_id[:50]}...</p>
                <p><strong>Model:</strong> {st.session_state.selected_model}</p>
                <p><strong>Language:</strong> {st.session_state.get('detected_language', 'Not detected')}</p>
                <p><strong>Project Type:</strong> {st.session_state.get('detected_project_type', 'Not detected')}</p>
                <p><strong>Goal:</strong> {st.session_state.initial_goal[:100]}...</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            # Calculate validation statistics
            total_files = len(st.session_state.audio_files)
            valid_files = sum(1 for result in st.session_state.audio_validation_results.values() 
                            if result.get('is_valid', False))
            total_duration = sum(result.get('duration', 0) for result in st.session_state.audio_validation_results.values())
            
            st.markdown(f"""
            <div class="stats-container">
                <div class="stat-card">
                    <h3>{total_files}</h3>
                    <p>Total Files</p>
                </div>
                <div class="stat-card">
                    <h3>{valid_files}</h3>
                    <p>Valid Files</p>
                </div>
                <div class="stat-card">
                    <h3>{total_duration:.1f}s</h3>
                    <p>Total Duration</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Email submission section
        st.markdown("---")
        st.subheader("📧 Submit Results")
        
        with st.form("submission_form"):
            user_email = st.text_input(
                "Email Address *",
                placeholder="your.email@domain.com",
                help="Enter your email address for submission tracking"
            )
            
            # Email validation display
            if user_email:
                if validate_email_against_spreadsheet(user_email):
                    st.markdown("""
                    <div class="success-message">
                        <strong>✅ Valid Email:</strong> Email format is valid and authorized.
                    </div>
                    """, unsafe_allow_html=True)
                    st.session_state.email_validated = True
                else:
                    st.markdown("""
                    <div class="error-message">
                        <strong>❌ Invalid Email:</strong> Email format is invalid or not authorized.
                    </div>
                    """, unsafe_allow_html=True)
                    st.session_state.email_validated = False
            else:
                st.session_state.email_validated = False
            
            submitted = st.form_submit_button(
                "📤 Submit Validation Results", 
                type="primary",
                disabled=not st.session_state.email_validated
            )
            
            if submitted and st.session_state.email_validated:
                with st.spinner("Submitting validation results..."):
                    # Prepare submission data
                    form_data = {
                        'timestamp': datetime.now().isoformat(),
                        'user_email': user_email,
                        'question_id': st.session_state.question_id,
                        'selected_model': st.session_state.selected_model,
                        'initial_goal': st.session_state.initial_goal,
                        'initial_prompt': st.session_state.initial_prompt,
                        'detected_language': st.session_state.get('detected_language'),
                        'detected_project_type': st.session_state.get('detected_project_type'),
                        'audio_files_count': len(st.session_state.audio_files),
                        'valid_files_count': valid_files,
                        'total_duration': total_duration,
                        'validation_results': st.session_state.audio_validation_results
                    }
                    
                    # Submit results (placeholder)
                    success = submit_validation_results(form_data)
                    
                    if success:
                        st.session_state.submission_complete = True
                        st.markdown("""
                        <div class="success-message">
                            <h4>✅ Submission Completed!</h4>
                            <p>Your audio validation results have been successfully submitted.</p>
                        </div>
                        """, unsafe_allow_html=True)
                        st.balloons()
                    else:
                        st.markdown("""
                        <div class="error-message">
                            <strong>❌ Submission Failed:</strong> Please try again later.
                        </div>
                        """, unsafe_allow_html=True)
        
        # Completion actions
        if st.session_state.get('submission_complete'):
            st.markdown("---")
            st.subheader("🎉 Validation Complete")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.success("✅ Results successfully submitted to tracking system!")
                st.info(f"📧 **Confirmation sent to:** {user_email}")
            
            with col2:
                if st.button("🔄 Start New Validation", type="primary"):
                    # Clear session state
                    keys_to_clear = [key for key in st.session_state.keys() if key not in ['current_page']]
                    for key in keys_to_clear:
                        del st.session_state[key]
                    st.session_state.current_page = "Metadata Input"
                    st.success("🆕 Ready for a new validation!")
                    st.rerun()
    
    elif page == "Help":
        st.header("❓ Help & Documentation")
        
        tab1, tab2, tab3 = st.tabs(["📋 Instructions", "🔧 Troubleshooting", "📊 Examples"])
        
        with tab1:
            st.markdown("""
            ### 📋 How to Use This App
            
            #### 1️⃣ Metadata Input
            - Enter the **Question ID** (unique identifier with language and project type)
            - Select the **Model** being evaluated (Gemini or ChatGPT)
            - Enter the **Initial Goal** and **Initial Prompt**
            - Upload **Audio Files** for validation (supports multiple formats)
            - Review **auto-detected language and project type** from Question ID
            
            #### 2️⃣ Audio Verification
            - Review populated metadata from Step 1
            - Click **Validate Audio Files** to perform comprehensive checks
            - Review validation results including:
              - Audio corruption detection
              - Duration validation (minimum 1 minute recommended)
              - Format and technical specifications
              - Placeholder for future transcription validation
            
            #### 3️⃣ Summary & Submission
            - Review complete **validation summary** with statistics
            - Enter your **email address** for submission tracking
            - **Submit validation results** to tracking system
            - Access placeholder functions for future Google Drive integration
            
            ### 🎵 Supported Audio Formats
            - WAV, MP3, M4A, FLAC, OGG, AAC
            - Maximum file size: 200MB per file
            - Minimum duration: 1 second (1 minute recommended)
            
            ### 🔍 Validation Checks
            - **Corruption Detection**: Verifies file integrity
            - **Playability**: Confirms audio can be loaded and processed
            - **Duration**: Checks minimum length requirements
            - **Format**: Validates audio specifications
            - **Transcription**: Placeholder for ASR integration
            """)
        
        with tab2:
            st.markdown("""
            ### 🔧 Troubleshooting
            
            #### Common Issues:
            - **Question ID parsing fails**: Ensure ID follows expected format with language and project type
            - **Audio validation errors**: Check file format and ensure files are not corrupted
            - **Email not validated**: Verify email format and authorization status
            - **Upload failures**: Ensure files are under size limit and in supported formats
            - **Navigation disabled**: Complete current step before proceeding to next
            
            #### Best Practices:
            - Use high-quality audio files with clear speech
            - Ensure consistent language between metadata and audio content
            - Test with a single file first before batch processing
            - Keep original audio files as backup before validation
            
            #### Regex Patterns Used:
            - **Language Detection**: `human_eval_([a-z]{2}-[A-Z]{2}|[a-z]{2}-\\d{3})\\+INTERNAL`
            - **Project Type Detection**: `experience_([a-z_]+)_human_eval`
            
            #### Validation Thresholds:
            - **Minimum Duration**: 1 second (hard limit)
            - **Recommended Duration**: 60 seconds
            - **Supported Sample Rates**: Any (automatically detected)
            - **Supported Channels**: Mono and Stereo
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
            
            #### Supported Languages:
            id-ID, ar-EG, ko-KR, es-419, pt-BR, hi-IN, en-IN, ja-JP, hi-EN, ko-EN, id-EN, vi-VN, pt-EN, de-DE, fr-FR, zh-CN, nl-NL, ru-EN, ja-KR, es-EN, zh-TW, ar-EN, zh-EN, fr-EN, ja-EN, de-EN, ko-JA, ko-ZH
            
            #### Project Types:
            - **Monolingual**: Single language audio content
            - **Audio Out**: Text-to-speech evaluation
            - **Mixed**: Code-mixed or multilingual content
            - **Language Learning**: Educational language content
            
            #### Validation Workflow:
            1. Parse Question ID → Extract metadata
            2. Upload audio files → Format validation
            3. Run validation → Technical analysis
            4. Review results → Quality assessment
            5. Submit → Track in system
            """)

if __name__ == "__main__":
    main()
