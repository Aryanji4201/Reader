# ACCURACY OPTIMIZED OMR SYSTEM - Version 2.0
import streamlit as st
import cv2
import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import Dict, List, Tuple

# Page configuration
st.set_page_config(
    page_title="OMR System v2.0 - High Accuracy",
    page_icon="🎯",
    layout="wide"
)

@dataclass
class OMRResult:
    student_id: str
    answers: Dict[int, str]
    scores: Dict[str, int]
    total: int
    confidence: float
    detected_answers: List[str]
    correct_answers: List[str]

class AccurateOMRProcessor:
    def __init__(self):
        # OPTIMIZED PARAMETERS FOR ACCURACY
        self.area_range = (15, 5000)
        self.fill_threshold = 0.20  # More conservative
        self.min_circularity = 0.3
        self.max_aspect_deviation = 0.7
        
        # EXACT ANSWER KEYS from Excel file SET-A
        self.answer_keys = {
            # Python (1-20)
            1:'A', 2:'C', 3:'C', 4:'C', 5:'C', 6:'A', 7:'C', 8:'C', 9:'B', 10:'C',
            11:'A', 12:'A', 13:'D', 14:'A', 15:'B', 16:'A', 17:'C', 18:'D', 19:'A', 20:'B',
            
            # Data Analysis (21-40)  
            21:'A', 22:'D', 23:'B', 24:'A', 25:'C', 26:'B', 27:'A', 28:'B', 29:'D', 30:'C',
            31:'C', 32:'A', 33:'B', 34:'C', 35:'A', 36:'B', 37:'D', 38:'B', 39:'A', 40:'B',
            
            # MySQL (41-60)
            41:'C', 42:'C', 43:'C', 44:'B', 45:'B', 46:'A', 47:'C', 48:'B', 49:'D', 50:'A',
            51:'C', 52:'B', 53:'C', 54:'C', 55:'A', 56:'B', 57:'B', 58:'A', 59:'A', 60:'B',
            
            # Power BI (61-80)
            61:'B', 62:'C', 63:'A', 64:'B', 65:'C', 66:'B', 67:'B', 68:'C', 69:'C', 70:'B',
            71:'B', 72:'B', 73:'D', 74:'B', 75:'A', 76:'B', 77:'B', 78:'B', 79:'B', 80:'B',
            
            # Statistics (81-100)
            81:'A', 82:'B', 83:'C', 84:'B', 85:'C', 86:'B', 87:'B', 88:'B', 89:'A', 90:'B',
            91:'C', 92:'B', 93:'C', 94:'B', 95:'B', 96:'B', 97:'C', 98:'A', 99:'B', 100:'C'
        }
        
        self.subject_ranges = {
            'Python': range(1, 21),
            'Data Analysis': range(21, 41), 
            'MySQL': range(41, 61),
            'Power BI': range(61, 81),
            'Advanced Statistics': range(81, 101)
        }
    
    def detect_bubbles(self, image):
        """Enhanced bubble detection with better filtering"""
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # Better preprocessing
        gray = cv2.bilateralFilter(gray, 9, 75, 75)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        bubbles = []
        for contour in contours:
            area = cv2.contourArea(contour)
            
            # Size filter
            if not (self.area_range[0] <= area <= self.area_range[1]):
                continue
            
            # Shape filters
            perimeter = cv2.arcLength(contour, True)
            if perimeter == 0:
                continue
                
            # Circularity check
            circularity = 4 * np.pi * area / (perimeter * perimeter)
            if circularity < self.min_circularity:
                continue
            
            # Aspect ratio check
            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = w / float(h)
            if abs(aspect_ratio - 1.0) > self.max_aspect_deviation:
                continue
            
            bubbles.append((x, y, w, h))
        
        # Sort bubbles by position (top to bottom, left to right)
        bubbles = sorted(bubbles, key=lambda b: (b[1], b[0]))
        
        st.info(f"🎯 Detected {len(bubbles)} high-quality bubbles")
        return bubbles
    
    def extract_answers_with_validation(self, image, bubbles):
        """Enhanced answer extraction with validation"""
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
            
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        answers = {}
        confidence_scores = []
        
        # Process bubbles in groups of 4
        for i in range(0, min(len(bubbles), 400), 4):
            if i + 3 >= len(bubbles):
                break
                
            question_num = (i // 4) + 1
            if question_num > 100:  # Only process first 100 questions
                break
                
            group = bubbles[i:i+4]
            # Sort by x position (left to right for A, B, C, D)
            group = sorted(group, key=lambda x: x[0])
            
            fills = []
            for j, (x, y, w, h) in enumerate(group):
                # Extract bubble region
                region = thresh[y:y+h, x:x+w]
                if region.size > 0:
                    fill_ratio = np.count_nonzero(region) / region.size
                    fills.append((j, fill_ratio))
            
            if fills:
                # Find most filled bubble
                fills.sort(key=lambda x: x[1], reverse=True)
                max_idx, max_fill = fills[0]
                
                # Check if significantly more filled than others
                second_fill = fills[1][1] if len(fills) > 1 else 0
                confidence = max_fill - second_fill
                
                if max_fill >= self.fill_threshold and confidence > 0.05:
                    answers[question_num] = chr(65 + max_idx)  # A, B, C, D
                    confidence_scores.append(confidence)
                else:
                    answers[question_num] = "BLANK"
                    confidence_scores.append(0.0)
        
        avg_confidence = np.mean(confidence_scores) if confidence_scores else 0.0
        
        st.info(f"🎯 Extracted {len([a for a in answers.values() if a != 'BLANK'])} confident answers")
        st.info(f"📊 Average confidence: {avg_confidence:.2f}")
        
        return answers, avg_confidence
    
    def calculate_scores_with_comparison(self, answers):
        """Calculate scores with detailed comparison"""
        scores = {}
        detected_answers = []
        correct_answers = []
        
        for subject, q_range in self.subject_ranges.items():
            subject_score = 0
            for q_num in q_range:
                detected = answers.get(q_num, "BLANK")
                correct = self.answer_keys.get(q_num, "?")
                
                detected_answers.append(detected)
                correct_answers.append(correct)
                
                if detected == correct:
                    subject_score += 1
            
            scores[subject] = subject_score
        
        return scores, detected_answers, correct_answers
    
    def process_omr(self, image_data, student_id):
        # Decode image
        nparr = np.frombuffer(image_data, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            st.error("Could not decode image")
            return None
        
        # Process with enhanced accuracy
        bubbles = self.detect_bubbles(image)
        answers, confidence = self.extract_answers_with_validation(image, bubbles)
        scores, detected, correct = self.calculate_scores_with_comparison(answers)
        total_score = sum(scores.values())
        
        return OMRResult(
            student_id=student_id,
            answers=answers,
            scores=scores,
            total=total_score,
            confidence=confidence,
            detected_answers=detected,
            correct_answers=correct
        )

# Initialize processor
if 'accurate_processor' not in st.session_state:
    st.session_state.accurate_processor = AccurateOMRProcessor()

# Main interface
st.title("🎯 OMR System v2.0 - High Accuracy Edition")
st.markdown("### Enhanced Detection • Correct Answer Keys • Validation")

# Input form
with st.form("accurate_omr_form"):
    col1, col2 = st.columns(2)
    
    with col1:
        student_id = st.text_input("Student ID", value="STU001")
    
    with col2:
        uploaded_file = st.file_uploader("Upload OMR Image", type=['jpg', 'jpeg', 'png'])
    
    process_btn = st.form_submit_button("🎯 Process with High Accuracy", use_container_width=True)

if process_btn and uploaded_file and student_id:
    with st.spinner("🎯 Processing with enhanced accuracy..."):
        result = st.session_state.accurate_processor.process_omr(uploaded_file.read(), student_id)
        
        if result:
            st.success("✅ High Accuracy Processing Complete!")
            
            # Display results with accuracy metrics
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                st.subheader("📊 Subject Scores")
                for subject, score in result.scores.items():
                    percentage = (score / 20) * 100
                    if percentage >= 90:
                        color = "🏆"
                    elif percentage >= 80:
                        color = "🟢"
                    elif percentage >= 60:
                        color = "🟡" 
                    else:
                        color = "🔴"
                    st.metric(f"{color} {subject}", f"{score}/20", f"{percentage:.1f}%")
            
            with col2:
                st.subheader("📈 Performance")
                total_percentage = (result.total / 100) * 100
                st.metric("**Total Score**", f"{result.total}/100", f"{total_percentage:.1f}%")
                st.metric("Confidence", f"{result.confidence:.2f}")
                
                # Grade with better thresholds
                if total_percentage >= 90:
                    st.success("🏆 Grade: A+")
                elif total_percentage >= 80:
                    st.success("🥇 Grade: A") 
                elif total_percentage >= 70:
                    st.info("🥈 Grade: B")
                elif total_percentage >= 60:
                    st.warning("🥉 Grade: C")
                else:
                    st.error("📚 Grade: D")
            
            with col3:
                st.subheader("🎯 Accuracy")
                total_correct = sum(1 for i, (d, c) in enumerate(zip(result.detected_answers, result.correct_answers)) if d == c and d != "BLANK")
                total_attempted = sum(1 for a in result.detected_answers if a != "BLANK")
                
                if total_attempted > 0:
                    accuracy = (total_correct / total_attempted) * 100
                    st.metric("Detection Accuracy", f"{accuracy:.1f}%")
                
                st.metric("Questions Attempted", total_attempted)
                st.metric("Correctly Detected", total_correct)
            
            # Detailed comparison
            with st.expander("🔍 Answer Comparison (First 20)", expanded=False):
                comparison_data = []
                for i in range(min(20, len(result.detected_answers))):
                    detected = result.detected_answers[i]
                    correct = result.correct_answers[i]
                    status = "✅" if detected == correct and detected != "BLANK" else "❌" if detected != "BLANK" else "⚪"
                    
                    comparison_data.append({
                        "Q": i + 1,
                        "Detected": detected,
                        "Correct": correct,
                        "Status": status
                    })
                
                if comparison_data:
                    df = pd.DataFrame(comparison_data)
                    st.dataframe(df, use_container_width=True)

st.markdown("---")
st.markdown("**v2.0 Features:** Enhanced detection • Exact answer keys • Confidence scoring • Answer validation")