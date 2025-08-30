"""
Tests for HTMLCompiler class - focus on actual functionality and edge cases.
"""

import pytest
import tempfile
from pathlib import Path
from grammarlee import HTMLCompiler, ChangeDetector


class TestHTMLCompiler:
    
    def test_html_escaping_prevents_xss(self):
        """Test that user text is properly escaped to prevent XSS."""
        detector = ChangeDetector()
        
        # Malicious input
        original = "Hello <script>alert('xss')</script> world"
        revised = "Hi <img src=x onerror=alert('xss')> world"
        
        session = detector.detect_changes(original, revised)
        compiler = HTMLCompiler()
        html = compiler.compile_to_html(session)
        
        # Key test: malicious JavaScript should be escaped and not executable
        # Check that dangerous content appears escaped (as &lt; instead of <)
        assert "&lt;" in html  # Some < characters should be escaped
        assert "&#x27;" in html or "&quot;" in html  # Quotes should be escaped
        
        # Most importantly: the raw malicious strings should not appear unescaped
        # These would be dangerous if they appeared unescaped in the HTML
        dangerous_strings = [
            "<script>alert(",  # Raw script tag
            "onerror=alert(",  # Raw event handler
            "javascript:",     # Javascript protocol
        ]
        
        for dangerous in dangerous_strings:
            assert dangerous not in html, f"Dangerous string '{dangerous}' found unescaped in HTML"
    
    def test_change_highlighting_accuracy(self):
        """Test that changes are highlighted correctly with proper IDs."""
        detector = ChangeDetector()
        original = "The cat sits"
        revised = "A dog runs"
        
        session = detector.detect_changes(original, revised)
        compiler = HTMLCompiler()
        
        text_html = compiler._generate_text_with_changes(session)
        
        # Should contain change markers with correct IDs
        for change in session.changes:
            assert f'id="text-{change.id}"' in text_html
            assert f'onclick="toggleChange({change.id},' in text_html
    
    def test_javascript_data_injection_safety(self):
        """Test that session data injected into JS is safe."""
        detector = ChangeDetector()
        
        # Text with quotes and special chars that could break JS
        original = 'Text with "quotes" and \n newlines'
        revised = "Text with 'quotes' and \\backslashes"
        
        session = detector.detect_changes(original, revised)
        compiler = HTMLCompiler()
        html = compiler.compile_to_html(session)
        
        # Should contain valid JSON without syntax errors
        assert "const changes = " in html
        # Should not break JS with unescaped quotes
        assert '\\"' in html or "\\'" in html
    
    def test_template_missing_fallback(self):
        """Test behavior when template file is missing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            compiler = HTMLCompiler(templates_dir=temp_dir)
            detector = ChangeDetector()
            session = detector.detect_changes("test", "testing")
            
            # Should raise error for missing template
            with pytest.raises(Exception):  # Jinja2 will raise TemplateNotFound
                compiler.compile_to_html(session, template_name="nonexistent.jinja")
    
    def test_large_text_performance(self):
        """Test that large texts don't cause performance issues."""
        detector = ChangeDetector()
        
        # Large text with many changes
        original = "word " * 1000
        revised = "term " * 1000
        
        session = detector.detect_changes(original, revised)
        compiler = HTMLCompiler()
        
        # Should complete without hanging
        html = compiler.compile_to_html(session)
        
        assert len(html) > 10000  # Should produce substantial output
        assert "change" in html
    
    def test_unicode_text_handling(self):
        """Test handling of Unicode characters."""
        detector = ChangeDetector()
        
        original = "Hello 世界 🌍"
        revised = "Hi 世界 🌎"
        
        session = detector.detect_changes(original, revised)
        compiler = HTMLCompiler()
        html = compiler.compile_to_html(session)
        
        # Unicode should be preserved
        assert "世界" in html
        assert "🌍" in html or "🌎" in html
