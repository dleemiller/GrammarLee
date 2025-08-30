"""
HTML compilation for LLM text editing interface.
"""

from __future__ import annotations
import html
import os
from typing import Optional
from pathlib import Path

try:
    from jinja2 import Environment, FileSystemLoader, Template
    HAS_JINJA2 = True
except ImportError:
    HAS_JINJA2 = False
    raise ImportError("jinja2 is required for HTML compilation")

from .models import TextEditSession


class HTMLCompiler:
    """Compiles TextEditSession to HTML interface for review."""
    
    def __init__(self, templates_dir: Optional[str] = None):
        """
        Initialize HTML compiler.
        
        Args:
            templates_dir: Directory containing Jinja2 templates. 
                          If None, uses default templates directory.
        """
        if templates_dir is None:
            # Default to templates directory relative to this file
            templates_dir = Path(__file__).parent / "templates"
        
        self.templates_dir = Path(templates_dir)
        
        if not self.templates_dir.exists():
            raise FileNotFoundError(f"Templates directory not found: {self.templates_dir}")
        
        self.env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=True
        )
    
    def compile_to_html(self, 
                       session: TextEditSession, 
                       title: str = "Review Text Changes",
                       template_name: str = "default.jinja") -> str:
        """
        Generate HTML interface for reviewing changes.
        
        Args:
            session: TextEditSession containing text and changes
            title: Page title
            template_name: Name of template to use
            
        Returns:
            Complete HTML document as string
        """
        # Prepare template data
        template_data = {
            'title': title,
            'original_text': session.original_text,
            'revised_text': session.revised_text,
            'changes': session.changes,
            'changes_count': len(session.changes),
            'text_with_changes': self._generate_text_with_changes(session),
            'changes_list_html': self._generate_changes_list_html(session.changes),
            'session_data': session.to_dict()  # Pass dict instead of JSON string
        }
        
        template = self.env.get_template(template_name)
        return template.render(**template_data)
    
    def _generate_text_with_changes(self, session: TextEditSession) -> str:
        """Generate HTML text with changes highlighted."""
        if not session.changes:
            return html.escape(session.original_text)  # Show original when no changes
        
        result = []
        last_pos = 0
        
        # Sort changes by position
        sorted_changes = sorted(session.changes, key=lambda c: c.start_pos)
        
        for change in sorted_changes:
            # Add text before this change (properly escaped)
            if change.start_pos > last_pos:
                result.append(html.escape(session.original_text[last_pos:change.start_pos]))
            
            # Add the change (with proper escaping of content)
            if change.type == "insert":
                result.append(
                    f'<span class="change insert" id="text-{change.id}" '
                    f'onclick="toggleChange({change.id}, \'accept\')">'
                    f'{html.escape(change.revised)}</span>'
                )
                last_pos = change.start_pos  # No movement for inserts
            elif change.type == "delete":
                result.append(
                    f'<span class="change delete" id="text-{change.id}" '
                    f'onclick="toggleChange({change.id}, \'reject\')">'
                    f'{html.escape(change.original)}</span>'
                )
                last_pos = change.end_pos
            elif change.type == "replace":
                result.append(
                    f'<span class="change replace" id="text-{change.id}" '
                    f'onclick="toggleChange({change.id}, \'accept\')">'
                    f'{html.escape(change.revised)}</span>'
                )
                last_pos = change.end_pos
        
        # Add remaining text (properly escaped)
        if last_pos < len(session.original_text):
            result.append(html.escape(session.original_text[last_pos:]))
        
        return ''.join(result)
    
    def _generate_changes_list_html(self, changes):
        """Generate HTML list of changes."""
        if not changes:
            return "<p>No changes detected.</p>"
        
        changes_html = []
        
        for change in changes:
            annotation_html = ""
            if change.annotation:
                annotation_html = f'<div class="annotation">{html.escape(change.annotation)}</div>'
            
            # Properly escape all text content
            original_text = html.escape(change.original) if change.original else "<em>none</em>"
            revised_text = html.escape(change.revised) if change.revised else "<em>deleted</em>"
            
            change_html = f"""
            <div class="change-item" id="change-{change.id}">
                <div class="change-header">
                    <span class="change-type {change.type}">{change.type}</span>
                    <div class="change-buttons">
                        <button class="btn accept" onclick="toggleChange({change.id}, 'accept')">Accept</button>
                        <button class="btn reject" onclick="toggleChange({change.id}, 'reject')">Reject</button>
                    </div>
                </div>
                <div class="change-text">
                    <div class="original">Original: {original_text}</div>
                    <div class="revised">Revised: {revised_text}</div>
                </div>
                {annotation_html}
            </div>
            """
            changes_html.append(change_html)
        
        return '\n'.join(changes_html)
