class ContentSplitter:
    """
    ContentSplitter is a class to parse the body of newsletter emails.
    It splits the content into sections based on common newsletter section patterns.
    """ 
    def __init__(self) -> None:
        # Common patterns that might indicate a section header
        self.section_patterns = [
            r'\n\s*[A-Z][A-Za-z\s&]+:',  # Capitalized words followed by colon
            r'\n\s*[A-Z][A-Za-z\s&]+\n',  # Capitalized words followed by newline
            r'\n\s*\d+\.\s+[A-Z]',  # Numbered sections
            r'\n\s*[•★✦]\s+[A-Z]',  # Bullet points followed by capital letter
        ]
        
    def find_section_boundaries(self, body: str) -> list[int]:
        """Find all potential section boundaries in the text"""
        import re
        boundaries = set()
        
        # Add start of text
        boundaries.add(0)
        
        # Find all potential section headers
        for pattern in self.section_patterns:
            matches = re.finditer(pattern, body)
            for match in matches:
                boundaries.add(match.start())
        
        # Convert to sorted list
        return sorted(list(boundaries))

    def parse(self, body: str) -> list[str]:
        """Parse the newsletter body into sections"""
        if not body:
            return []
            
        boundaries = self.find_section_boundaries(body)
        
        # If no sections found, return the whole body as one section
        if len(boundaries) <= 1:
            return [body.strip()]
            
        sections = []
        for i in range(len(boundaries)):
            if i == len(boundaries) - 1:
                section = body[boundaries[i]:].strip()
            else:
                section = body[boundaries[i]:boundaries[i+1]].strip()
            
            if section:  # Only add non-empty sections
                sections.append(section)
        
        return sections

