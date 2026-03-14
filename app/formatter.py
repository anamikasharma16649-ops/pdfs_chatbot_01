# import re

# def format_text(text: str) -> str:
#     if not text or not text.strip():
#         return "No answer generated."
    
#     lines = text.splitlines()
#     cleaned_lines = []
    
#     for line in lines:
#         line = line.strip()
#         if line:  
#             cleaned_lines.append(line)
    
#     text = "\n".join(cleaned_lines)
#     sections = re.split(r'\n\s*\n', text)
    
#     formatted_sections = []
    
#     for section in sections:
#         if not section.strip():
#             continue
            
#         lines = section.split('\n')
#         section_formatted = []
        
#         for line in lines:
#             line = line.strip()
#             if not line:
#                 continue
            
#             numbered_match = re.match(r'^(\d+\.)\s*(.*)', line)
#             if numbered_match:
#                 num, content = numbered_match.groups()
#                 # 🔥 FIX: Sirf headings ko underline karo
#                 if len(content.split()) <= 4 or content.isupper() or content.istitle():
#                     section_formatted.append(f"<br><b><u>{num} {content}</u></b>")
#                 else:
#                     section_formatted.append(f"<br><b>{num}</b> {content}")
#                 continue
            
#             if line.startswith('- ') or line.startswith('• ') or line.startswith('* '):
#                 content = re.sub(r'^[-•*]\s*', '', line)
#                 section_formatted.append(f"• {content}")
#                 continue
            
#             # 🔥 FIX: Headings ko underline karo
#             if line.endswith(':') and len(line.split()) <= 5:
#                 clean = line.replace(":", "")
#                 section_formatted.append(f"<br><b><u>{clean}</u></b>")
#             elif line.isupper() or (line[0].isupper() and len(line.split()) <= 3) or line.istitle():
#                 if line.startswith('**') and line.endswith('**'):
#                     section_formatted.append(f"<br><b><u>{line[2:-2]}</u></b>")
#                 else:
#                     section_formatted.append(f"<br><b><u>{line}</u></b>")
#             else:
#                 # 🔥 IMPORTANT: Normal text mein kabhi <u> tag mat lagao
#                 if '**' in line:
#                     line = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', line)
#                 # Remove any existing <u> tags
#                 line = re.sub(r'<u>(.*?)</u>', r'\1', line)
#                 section_formatted.append(line)
        
#         formatted_sections.append("<br>".join(section_formatted))
    
#     result = "<br><br>".join(formatted_sections)
    
#     result = re.sub(r'(<br>\s*){3,}', '<br><br>', result)
#     result = re.sub(r'•\s+', '• ', result)
    
#     return result.strip()

import re

def format_text(text: str) -> str:
    if not text or not text.strip():
        return "No answer generated."
    
    lines = text.splitlines()
    cleaned_lines = []
    
    for line in lines:
        line = line.strip()
        if line:  
            cleaned_lines.append(line)
    
    text = "\n".join(cleaned_lines)
    sections = re.split(r'\n\s*\n', text)
    
    formatted_sections = []
    
    for section in sections:
        if not section.strip():
            continue
            
        lines = section.split('\n')
        section_formatted = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 🔥 NUMBERED LISTS KO BULLETS MEIN BADLO
            numbered_match = re.match(r'^(\d+\.)\s*(.*)', line)
            if numbered_match:
                num, content = numbered_match.groups()
                # Sirf content lo, number hatao, bullet lagao
                section_formatted.append(f"<br>• {content}")
                continue
            
            # Bullet points handle karo
            if line.startswith('- ') or line.startswith('• ') or line.startswith('* '):
                content = re.sub(r'^[-•*]\s*', '', line)
                section_formatted.append(f"• {content}")
                continue
            
            # Headings handle karo
            if line.endswith(':') and len(line.split()) <= 5:
                clean = line.replace(":", "")
                section_formatted.append(f"<br><b><u>{clean}</u></b>")
            elif line.isupper() or (line[0].isupper() and len(line.split()) <= 3) or line.istitle():
                if line.startswith('**') and line.endswith('**'):
                    section_formatted.append(f"<br><b><u>{line[2:-2]}</u></b>")
                else:
                    section_formatted.append(f"<br><b><u>{line}</u></b>")
            else:
                # Normal text
                if '**' in line:
                    line = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', line)
                line = re.sub(r'<u>(.*?)</u>', r'\1', line)
                section_formatted.append(line)
        
        formatted_sections.append("<br>".join(section_formatted))
    
    result = "<br><br>".join(formatted_sections)
    
    # Clean up extra line breaks
    result = re.sub(r'(<br>\s*){3,}', '<br><br>', result)
    result = re.sub(r'•\s+', '• ', result)
    
    return result.strip()

    