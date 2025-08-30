"""
LLM Text Editor - A library for tracking and reviewing text changes made by LLMs.
"""

from .models import Change, TextEditSession
from .editor import ChangeDetector
from .html import HTMLCompiler

__version__ = "0.1.0"

__all__ = [
    "Change",
    "TextEditSession", 
    "ChangeDetector",
    "HTMLCompiler"
]


class LLMTextEditor:
    """
    Main interface for LLM text editing with change tracking.
    
    This is a convenience class that combines the functionality of
    ChangeDetector and HTMLCompiler for easy use.
    """
    
    def __init__(self, templates_dir=None):
        """
        Initialize the LLM text editor.
        
        Args:
            templates_dir: Optional custom templates directory path
        """
        self.detector = ChangeDetector()
        self.compiler = HTMLCompiler(templates_dir)
        self.current_session = None
    
    def detect_changes(self, original: str, revised: str) -> TextEditSession:
        """
        Detect changes between original and revised text.
        
        Args:
            original: The original text
            revised: The LLM-edited text
            
        Returns:
            TextEditSession containing the detected changes
        """
        self.current_session = self.detector.detect_changes(original, revised)
        return self.current_session
    
    def add_annotation(self, change_id: int, annotation: str) -> bool:
        """
        Add an annotation to a specific change.
        
        Args:
            change_id: ID of the change to annotate
            annotation: Annotation text (typically from a second LLM pass)
            
        Returns:
            True if annotation was added successfully, False otherwise
        """
        if not self.current_session:
            return False
        return self.detector.add_annotation(self.current_session, change_id, annotation)
    
    def apply_decisions(self, decisions: dict) -> str:
        """
        Apply user accept/reject decisions to generate final text.
        
        Args:
            decisions: Dict mapping change_id -> "accept" | "reject"
            
        Returns:
            Final text with decisions applied
        """
        if not self.current_session:
            raise ValueError("No current session. Call detect_changes() first.")
        return self.detector.apply_user_decisions(self.current_session, decisions)
    
    def compile_to_html(self, title: str = "Review Text Changes", 
                       template_name: str = "default.jinja") -> str:
        """
        Generate HTML interface for reviewing changes.
        
        Args:
            title: Page title
            template_name: Name of template to use
            
        Returns:
            Complete HTML document as string
        """
        if not self.current_session:
            raise ValueError("No current session. Call detect_changes() first.")
        return self.compiler.compile_to_html(self.current_session, title, template_name)
