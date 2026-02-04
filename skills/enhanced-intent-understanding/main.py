#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced Intent Understanding Skill
Enhanced intent understanding with contextual awareness and confidence scoring
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import json
import logging
from datetime import datetime

# Add project paths
project_root = Path(__file__).parent.parent.parent
claude_skills_root = project_root / ".claude" / "skills"

# Add to Python path
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / ".claude" / "skills"))

# Import base skill interface
try:
    from common.skill_interface import SkillInterface
except ImportError:
    # Fallback to a simple interface
    class SkillInterface:
        def __init__(self):
            pass

# Import intent understanding from the original skill
try:
    from intent_understanding.main import IntentUnderstandingSkill
    INTENT_UNDERSTANDING_AVAILABLE = True
except ImportError:
    INTENT_UNDERSTANDING_AVAILABLE = False

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedIntentUnderstandingSkill:
    """Enhanced Intent Understanding Skill with contextual awareness and confidence scoring"""

    def __init__(self):
        # No parent class to initialize
        pass
        self.contextual_understanding = True
        self.emotion_recognition = True
        self.intent_confidence_scoring = True
        self.context_memory = ContextMemorySystem()

        # Initialize the original intent understanding skill if available
        if INTENT_UNDERSTANDING_AVAILABLE:
            self.original_intent_skill = IntentUnderstandingSkill()
        else:
            self.original_intent_skill = None
            logger.warning("Original intent-understanding skill not available, using basic implementation")

    def analyze_intent(self, input_text: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Enhanced intent analysis with contextual awareness and confidence scoring

        Args:
            input_text: The input text to analyze
            context: Optional context information

        Returns:
            Dict containing:
            - intent: The recognized intent
            - confidence: Confidence score (0-1)
            - context: Context information
            - emotion: Detected emotion (if enabled)
            - original_intent: Original intent from base skill (if available)
        """
        try:
            # Enhanced intent recognition
            intent = self._recognize_intent(input_text)

            # Contextual information
            context_info = self.context_memory.get_context(context) if context else {}

            # Emotion recognition (optional)
            emotion = self._recognize_emotion(input_text) if self.emotion_recognition else None

            # Original intent from base skill (if available)
            original_intent = None
            if self.original_intent_skill:
                try:
                    original_intent = self.original_intent_skill.analyze_intent(input_text)
                except Exception as e:
                    logger.warning(f"Failed to get original intent: {e}")

            # Confidence scoring
            confidence = self._calculate_confidence(intent, context_info, emotion, original_intent)

            return {
                'intent': intent,
                'confidence': confidence,
                'context': context_info,
                'emotion': emotion,
                'original_intent': original_intent
            }

        except Exception as e:
            logger.error(f"Error in intent analysis: {e}")
            # Fallback to basic analysis
            return {
                'intent': 'unknown',
                'confidence': 0.0,
                'context': context_info if 'context_info' in locals() else {},
                'emotion': emotion if 'emotion' in locals() else None,
                'original_intent': original_intent if 'original_intent' in locals() else None,
                'error': str(e)
            }

    def _recognize_intent(self, text: str) -> str:
        """Enhanced intent recognition with contextual awareness"""
        # Use original skill if available
        if self.original_intent_skill:
            try:
                result = self.original_intent_skill.analyze_intent(text)
                if isinstance(result, dict) and 'intent' in result:
                    return result['intent']
                else:
                    return str(result)
            except Exception as e:
                logger.warning(f"Original intent skill failed: {e}")

        # Fallback to basic intent recognition
        return self._basic_intent_recognition(text)

    def _basic_intent_recognition(self, text: str) -> str:
        """Basic intent recognition when original skill is not available"""
        # Simple keyword-based intent recognition
        text_lower = text.lower()

        # Check for common intent patterns
        if any(keyword in text_lower for keyword in ['analyze', 'analyze', 'examine', 'review']):
            return 'analyze_request'
        elif any(keyword in text_lower for keyword in ['explain', 'describe', 'clarify', 'understand']):
            return 'explanation_request'
        elif any(keyword in text_lower for keyword in ['create', 'generate', 'produce', 'make']):
            return 'creation_request'
        elif any(keyword in text_lower for keyword in ['fix', 'solve', 'resolve', 'correct']):
            return 'problem_solving_request'
        elif any(keyword in text_lower for keyword in ['help', 'assist', 'support', 'support']):
            return 'help_request'
        elif any(keyword in text_lower for keyword in ['information', 'data', 'details', 'info']):
            return 'information_request'
        else:
            return 'general_request'

    def _recognize_emotion(self, text: str) -> Optional[str]:
        """Emotion recognition from text (simplified implementation)"""
        # This is a simplified emotion recognition
        # In a real implementation, you would use a more sophisticated NLP model
        text_lower = text.lower()

        # Simple emotion detection based on keywords
        if any(word in text_lower for word in ['happy', 'great', 'good', 'excellent', 'wonderful', 'fantastic']):
            return 'positive'
        elif any(word in text_lower for word in ['sad', 'bad', 'terrible', 'awful', 'horrible', 'disappointing']):
            return 'negative'
        elif any(word in text_lower for word in ['angry', 'frustrated', 'annoyed', 'upset', 'mad', 'furious']):
            return 'angry'
        elif any(word in text_lower for word in ['confused', 'unclear', 'confusing', 'puzzled', 'bewildered']):
            return 'confused'
        else:
            return 'neutral'

    def _calculate_confidence(self, intent: str, context: Dict, emotion: Optional[str], original_intent: Optional[Dict]) -> float:
        """Calculate confidence score for intent understanding"""
        confidence_factors = []

        # Factor 1: Intent recognition confidence
        confidence_factors.append(self._get_intent_confidence(intent))

        # Factor 2: Context consistency
        confidence_factors.append(self._get_context_confidence(context))

        # Factor 3: Emotion consistency (if emotion recognition is enabled)
        if self.emotion_recognition:
            confidence_factors.append(self._get_emotion_confidence(intent, emotion))

        # Factor 4: Original intent alignment (if available)
        if original_intent and isinstance(original_intent, dict):
            confidence_factors.append(self._get_original_intent_alignment(intent, original_intent))

        # Calculate weighted average
        if confidence_factors:
            confidence = sum(confidence_factors) / len(confidence_factors)
        else:
            confidence = 0.5  # Default confidence

        # Ensure confidence is between 0 and 1
        return max(0.0, min(1.0, confidence))

    def _get_intent_confidence(self, intent: str) -> float:
        """Get confidence based on intent recognition quality"""
        # This would be more sophisticated in a real implementation
        if intent and intent != 'unknown':
            return 0.9
        else:
            return 0.1

    def _get_context_confidence(self, context: Dict) -> float:
        """Get confidence based on context quality"""
        # Higher confidence if context is rich and relevant
        context_keys = set(context.keys()) if isinstance(context, dict) else set()
        if 'user_id' in context_keys and 'session_id' in context_keys:
            return 0.8
        elif context_keys:
            return 0.6
        else:
            return 0.3

    def _get_emotion_confidence(self, intent: str, emotion: Optional[str]) -> float:
        """Get confidence based on emotion consistency"""
        if emotion == 'neutral':
            return 0.8  # Neutral emotion provides stable context
        elif emotion in ['positive', 'negative']:
            return 0.7  # Emotional context provides additional information
        else:
            return 0.5  # No emotion detected

    def _get_original_intent_alignment(self, intent: str, original_intent: Dict) -> float:
        """Get confidence based on alignment with original intent"""
        if isinstance(original_intent, dict) and 'intent' in original_intent:
            original_confidence = original_intent.get('confidence', 0.0)
            if original_confidence > 0.7:
                return 0.9
            else:
                return 0.8
        else:
            return 0.5

    def store_context(self, context_data: Dict[str, Any]) -> bool:
        """Store context information"""
        try:
            self.context_memory.store_context(context_data)
            return True
        except Exception as e:
            logger.error(f"Error storing context: {e}")
            return False

    def retrieve_context(self, context_type: str, user_id: Optional[str] = None) -> Optional[Dict]:
        """Retrieve context information"""
        try:
            return self.context_memory.retrieve_context(context_type, user_id)
        except Exception as e:
            logger.error(f"Error retrieving context: {e}")
            return None

    def update_preferences(self, user_id: str, preferences: Dict[str, Any]) -> bool:
        """Update user preferences"""
        try:
            self.context_memory.update_preferences(user_id, preferences)
            return True
        except Exception as e:
            logger.error(f"Error updating preferences: {e}")
            return False


class ContextMemorySystem:
    """Context memory system for storing and retrieving context information"""

    def __init__(self):
        self.short_term_memory = {}  # Short-term conversation memory
        self.long_term_memory = {}   # Long-term experience storage
        self.session_context = {}    # Session context
        self.user_preferences = {}   # User preferences

        # Initialize memory structures
        self.short_term_memory = {
            'recent_interactions': [],
            'contextual_history': [],
            'interaction_summary': {}
        }
        self.long_term_memory = {}
        self.session_context = {}
        self.user_preferences = {}

    def store_context(self, context_data: Dict[str, Any]) -> bool:
        """Store context information"""
        try:
            # Store in short-term memory
            if 'user_id' in context_data:
                user_id = context_data['user_id']
                if user_id not in self.short_term_memory['recent_interactions']:
                    self.short_term_memory['recent_interactions'].append(user_id)
                    # Limit to last 10 interactions per user
                    if len(self.short_term_memory['recent_interactions']) > 10:
                        self.short_term_memory['recent_interactions'] = self.short_term_memory['recent_interactions'][-10:]

            # Store in session context
            session_id = context_data.get('session_id')
            if session_id:
                if session_id not in self.session_context:
                    self.session_context[session_id] = {}
                self.session_context[session_id].update(context_data)

            # Store in user preferences if specified
            if 'preferences' in context_data:
                user_id = context_data.get('user_id')
                if user_id:
                    if user_id not in self.user_preferences:
                        self.user_preferences[user_id] = {}
                    self.user_preferences[user_id].update(context_data['preferences'])

            # Add to contextual history
            self.short_term_memory['contextual_history'].append({
                'timestamp': str(datetime.now()),
                'context': context_data
            })
            # Limit to last 50 historical entries
            if len(self.short_term_memory['contextual_history']) > 50:
                self.short_term_memory['contextual_history'] = self.short_term_memory['contextual_history'][-50:]

            return True
        except Exception as e:
            logger.error(f"Error storing context: {e}")
            return False

    def retrieve_context(self, context_type: str, user_id: Optional[str] = None) -> Optional[Dict]:
        """Retrieve context information"""
        try:
            if context_type == 'short_term':
                return self.short_term_memory.copy()
            elif context_type == 'user_preferences' and user_id:
                return self.user_preferences.get(user_id, {})
            elif context_type == 'session_context':
                return self.session_context.copy()
            elif context_type == 'long_term':
                return self.long_term_memory.copy()
            else:
                return {}
        except Exception as e:
            logger.error(f"Error retrieving context: {e}")
            return None

    def update_preferences(self, user_id: str, preferences: Dict[str, Any]) -> bool:
        """Update user preferences"""
        try:
            if user_id not in self.user_preferences:
                self.user_preferences[user_id] = {}
            self.user_preferences[user_id].update(preferences)
            return True
        except Exception as e:
            logger.error(f"Error updating preferences: {e}")
            return False




# Main execution function for standalone usage
def main():
    """Main execution function for testing the enhanced intent understanding skill"""
    print("Enhanced Intent Understanding Skill")
    print("=" * 40)

    # Initialize the skill
    skill = EnhancedIntentUnderstandingSkill()

    # Test with sample inputs
    test_inputs = [
        "Can you analyze the sales module for me?",
        "I need help understanding how inventory works",
        "Could you explain the accounting features?",
        "That's great! Now can you show me how to fix the issue?",
        "I'm confused about the procurement process"
    ]

    print("Testing enhanced intent understanding capabilities:")
    print()

    for i, test_input in enumerate(test_inputs, 1):
        print(f"Test {i}: {test_input}")

        # Analyze intent
        result = skill.analyze_intent(test_input)

        print(f"  Intent: {result.get('intent', 'N/A')}")
        print(f"  Confidence: {result.get('confidence', 0):.2f}")
        print(f"  Emotion: {result.get('emotion', 'N/A')}")
        if 'original_intent' in result and result['original_intent']:
            print(f"  Original Intent: {result['original_intent']}")
        print()

    print("Enhanced Intent Understanding Skill test completed.")


if __name__ == "__main__":
    main()