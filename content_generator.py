from typing import List, Dict, Any
from ..core import BaseAgent, Task
from loguru import logger
import asyncio

class ContentGeneratorAgent(BaseAgent):
    def __init__(self, agent_id: str = None, name: str = None):
        super().__init__(agent_id, name or "ContentGeneratorAgent")
    
    def get_capabilities(self) -> List[str]:
        return [
            "content_generation",
            "text_writing",
            "article_creation",
            "summary_writing",
            "creative_writing",
            "technical_writing",
            "content_planning"
        ]
    
    def _initialize_tools(self):
        """Initialize content generation tools"""
        self.tools = {
            "generate_article": self.generate_article,
            "write_summary": self.write_summary,
            "create_outline": self.create_outline,
            "generate_titles": self.generate_titles,
            "format_content": self.format_content
        }
    
    async def process_task(self, task: Task) -> Any:
        """Process content generation task"""
        try:
            parameters = task.parameters
            content_type = parameters.get("content_type", "article")
            topic = parameters.get("topic", task.description)
            length = parameters.get("length", "medium")  # short, medium, long
            tone = parameters.get("tone", "neutral")  # formal, casual, professional, creative
            target_audience = parameters.get("target_audience", "general")
            
            # Generate content based on type
            if content_type == "article":
                result = await self.generate_article(topic, length, tone, target_audience)
            elif content_type == "summary":
                result = await self.write_summary(topic, length, tone)
            elif content_type == "outline":
                result = await self.create_outline(topic, length)
            elif content_type == "titles":
                result = await self.generate_titles(topic)
            elif content_type == "creative":
                result = await self.generate_creative_content(topic, length, tone)
            else:
                result = await self.generate_article(topic, length, tone, target_audience)
            
            return {
                "content_type": content_type,
                "topic": topic,
                "length": length,
                "tone": tone,
                "target_audience": target_audience,
                "generated_content": result,
                "word_count": len(result.split()) if isinstance(result, str) else 0,
                "character_count": len(result) if isinstance(result, str) else 0
            }
            
        except Exception as e:
            logger.error(f"Content generation failed: {str(e)}")
            raise e
    
    async def generate_article(self, topic: str, length: str = "medium", 
                             tone: str = "neutral", audience: str = "general") -> str:
        """Generate an article on the given topic"""
        
        # Determine article length
        length_map = {
            "short": {"paragraphs": 2, "sentences_per_paragraph": 3},
            "medium": {"paragraphs": 4, "sentences_per_paragraph": 4},
            "long": {"paragraphs": 6, "sentences_per_paragraph": 5}
        }
        
        target = length_map.get(length, length_map["medium"])
        
        # Generate article structure
        article_parts = []
        
        # Title
        title = await self._generate_title(topic, tone)
        article_parts.append(f"# {title}\n")
        
        # Introduction
        intro = await self._generate_introduction(topic, audience, tone)
        article_parts.append(f"## Introduction\n{intro}\n")
        
        # Main body paragraphs
        main_points = await self._generate_main_points(topic, target["paragraphs"] - 2)
        
        for i, point in enumerate(main_points, 1):
            paragraph = await self._expand_point(point, target["sentences_per_paragraph"], tone)
            article_parts.append(f"## {point}\n{paragraph}\n")
        
        # Conclusion
        conclusion = await self._generate_conclusion(topic, tone)
        article_parts.append(f"## Conclusion\n{conclusion}")
        
        return "\n".join(article_parts)
    
    async def write_summary(self, topic: str, length: str = "medium", tone: str = "neutral") -> str:
        """Write a summary on the given topic"""
        
        length_map = {
            "short": 50,    # words
            "medium": 150,
            "long": 300
        }
        
        target_words = length_map.get(length, 150)
        
        # Generate key points about the topic
        key_points = await self._generate_key_points(topic, 3)
        
        # Combine into summary
        summary_parts = []
        
        # Opening sentence
        opening = f"This summary explores {topic}, "
        if tone == "formal":
            opening += "examining its key aspects and implications."
        elif tone == "casual":
            opening += "looking at what makes it interesting and important."
        else:
            opening += "covering its main features and significance."
        
        summary_parts.append(opening)
        
        # Add key points
        for point in key_points:
            if tone == "formal":
                sentence = f"Furthermore, {point.lower()}."
            elif tone == "casual":
                sentence = f"You'll also find that {point.lower()}."
            else:
                sentence = f"Additionally, {point.lower()}."
            
            summary_parts.append(sentence)
        
        # Closing
        if tone == "formal":
            closing = "These elements collectively provide a comprehensive understanding of the subject matter."
        elif tone == "casual":
            closing = "All these factors come together to show why this topic matters."
        else:
            closing = "Together, these aspects offer valuable insights into the topic."
        
        summary_parts.append(closing)
        
        summary = " ".join(summary_parts)
        
        # Adjust length if needed
        words = summary.split()
        if len(words) > target_words * 1.2:
            # Trim down
            summary = " ".join(words[:target_words])
        elif len(words) < target_words * 0.8:
            # Expand slightly
            summary += f" In conclusion, {topic} represents an important area that warrants further consideration and study."
        
        return summary
    
    async def create_outline(self, topic: str, length: str = "medium") -> Dict[str, Any]:
        """Create an outline for content about the topic"""
        
        length_map = {
            "short": 3,
            "medium": 5,
            "long": 8
        }
        
        num_sections = length_map.get(length, 5)
        
        # Generate main sections
        main_sections = await self._generate_main_points(topic, num_sections)
        
        outline = {
            "title": await self._generate_title(topic, "neutral"),
            "topic": topic,
            "sections": []
        }
        
        for i, section in enumerate(main_sections, 1):
            # Generate subsections for each main section
            subsections = await self._generate_subsections(section, 2)
            
            outline["sections"].append({
                "order": i,
                "title": section,
                "subsections": subsections
            })
        
        return outline
    
    async def generate_titles(self, topic: str) -> List[str]:
        """Generate multiple title options for the topic"""
        
        title_templates = [
            "Understanding {topic}: A Comprehensive Guide",
            "The Complete Guide to {topic}",
            "{topic}: What You Need to Know",
            "Exploring {topic}: Key Insights and Analysis",
            "{topic} Demystified: Expert Perspectives",
            "The Future of {topic}: Trends and Predictions",
            "Mastering {topic}: Strategies and Best Practices",
            "{topic} Explained: From Basics to Advanced"
        ]
        
        titles = []
        for template in title_templates:
            title = template.format(topic=topic.title())
            titles.append(title)
        
        # Add some creative variations
        creative_titles = [
            f"{topic.title()}: The Ultimate Resource",
            f"Everything About {topic.title()} in One Place",
            f"Your Guide to Understanding {topic.title()}",
            f"{topic.title()}: Insights and Overview"
        ]
        
        titles.extend(creative_titles)
        
        return titles[:10]  # Return top 10
    
    async def generate_creative_content(self, topic: str, length: str = "medium", tone: str = "creative") -> str:
        """Generate creative content (story, narrative, etc.)"""
        
        # This is a simplified creative content generator
        # In practice, you might use AI models for more sophisticated content
        
        creative_templates = {
            "story": "Once upon a time, in the world of {topic}, something extraordinary happened...",
            "narrative": "The journey into {topic} begins with a single step, where possibilities become realities...",
            "poetic": "In the realm of {topic}, where ideas dance and concepts bloom, we find ourselves at the crossroads of innovation..."
        }
        
        # Choose a template based on topic and tone
        if "story" in topic.lower() or tone == "narrative":
            template = creative_templates["story"]
        elif tone == "poetic":
            template = creative_templates["poetic"]
        else:
            template = creative_templates["narrative"]
        
        # Generate the creative piece
        content = template.format(topic=topic)
        
        # Add more content based on length
        if length == "short":
            content += " This brief glimpse into {topic} reveals its fascinating nature."
        elif length == "medium":
            content += f" As we delve deeper into {topic}, we discover layers of meaning and complexity that challenge our perceptions and inspire new ways of thinking."
        else:  # long
            content += f" As we delve deeper into {topic}, we discover layers of meaning and complexity that challenge our perceptions and inspire new ways of thinking. The journey through this landscape of ideas reveals not just facts and figures, but the very essence of what makes {topic} so compelling and relevant to our modern world."
        
        return content
    
    async def format_content(self, content: str, format_type: str = "markdown") -> str:
        """Format content according to specified format"""
        
        if format_type == "html":
            # Simple markdown to HTML conversion
            lines = content.split('\n')
            html_lines = []
            
            for line in lines:
                if line.startswith('# '):
                    html_lines.append(f'<h1>{line[2:]}</h1>')
                elif line.startswith('## '):
                    html_lines.append(f'<h2>{line[3:]}</h2>')
                elif line.startswith('### '):
                    html_lines.append(f'<h3>{line[4:]}</h3>')
                elif line.strip() == '':
                    html_lines.append('<br>')
                else:
                    html_lines.append(f'<p>{line}</p>')
            
            return '\n'.join(html_lines)
        
        elif format_type == "plain":
            # Remove markdown formatting
            import re
            plain = re.sub(r'#+\s*', '', content)  # Remove headers
            plain = re.sub(r'\*\*(.*?)\*\*', r'\1', plain)  # Remove bold
            plain = re.sub(r'\*(.*?)\*', r'\1', plain)  # Remove italic
            return plain
        
        else:
            return content  # Return as-is (markdown)
    
    # Helper methods
    
    async def _generate_title(self, topic: str, tone: str) -> str:
        """Generate a title for the content"""
        
        if tone == "formal":
            return f"An Analysis of {topic.title()}"
        elif tone == "casual":
            return f"Getting to Know {topic.title()}"
        elif tone == "creative":
            return f"Exploring the World of {topic.title()}"
        else:
            return f"Understanding {topic.title()}"
    
    async def _generate_introduction(self, topic: str, audience: str, tone: str) -> str:
        """Generate an introduction paragraph"""
        
        if audience == "technical":
            return f"{topic.title()} represents a significant area of study that warrants detailed examination. This analysis explores the technical aspects, implementation considerations, and practical applications relevant to professionals in the field."
        elif audience == "beginner":
            return f"Welcome to the world of {topic}! This guide is designed to help you understand the fundamentals and get started with confidence. We'll walk through the key concepts in a way that's easy to grasp and apply."
        else:
            return f"{topic.title()} has become increasingly important in today's landscape. This comprehensive overview examines its key aspects, benefits, and applications to provide readers with a solid understanding of the subject."
    
    async def _generate_main_points(self, topic: str, count: int) -> List[str]:
        """Generate main points for the content"""
        
        # Generic main points that can be adapted to any topic
        base_points = [
            f"Key Concepts and Terminology",
            f"Historical Context and Development",
            f"Practical Applications and Use Cases",
            f"Benefits and Advantages",
            f"Challenges and Considerations",
            f"Future Trends and Outlook",
            f"Best Practices and Recommendations",
            f"Tools and Resources"
        ]
        
        return base_points[:count]
    
    async def _expand_point(self, point: str, sentences: int, tone: str) -> str:
        """Expand a point into a full paragraph"""
        
        sentence_templates = {
            "formal": [
                f"{point} requires careful consideration and analysis.",
                f"The implications of {point.lower()} extend across multiple domains.",
                f"Research indicates that {point.lower()} plays a crucial role.",
                f"Further investigation into {point.lower()} reveals additional complexities."
            ],
            "casual": [
                f"When we look at {point.lower()}, there's a lot to consider.",
                f"It's interesting to see how {point.lower()} affects different situations.",
                f"Many people find that {point.lower()} is more important than they initially thought.",
                f"The practical side of {point.lower()} really shows its value in everyday scenarios."
            ],
            "neutral": [
                f"{point} represents an important aspect that deserves attention.",
                f"The role of {point.lower()} cannot be overlooked in comprehensive analysis.",
                f"Understanding {point.lower()} provides valuable insights into the broader context.",
                f"Various factors influence how {point.lower()} manifests in different environments."
            ]
        }
        
        templates = sentence_templates.get(tone, sentence_templates["neutral"])
        
        # Create paragraph with specified number of sentences
        paragraph_sentences = templates[:sentences]
        
        # Add some variation
        if sentences > len(paragraph_sentences):
            paragraph_sentences.append(f"This dimension of {point.lower()} offers additional perspectives worth exploring.")
        
        return " ".join(paragraph_sentences)
    
    async def _generate_conclusion(self, topic: str, tone: str) -> str:
        """Generate a conclusion paragraph"""
        
        if tone == "formal":
            return f"In conclusion, {topic} represents a multifaceted subject that requires ongoing research and analysis. The insights presented here provide a foundation for further investigation and practical application in relevant fields."
        elif tone == "casual":
            return f"To wrap up, {topic} offers plenty of interesting angles to explore. Whether you're just getting started or looking to deepen your understanding, there's always more to discover and apply."
        else:
            return f"In summary, {topic} encompasses various important elements that contribute to its overall significance. The key takeaways presented here serve as a valuable reference for continued learning and application."
    
    async def _generate_key_points(self, topic: str, count: int) -> List[str]:
        """Generate key points about a topic"""
        
        # Generic key points that can be adapted
        generic_points = [
            f"{topic} has significant practical applications",
            f"Understanding {topic} requires comprehensive analysis",
            f"The benefits of {topic} are well-documented",
            f"Future developments in {topic} show promising potential",
            f"Best practices for {topic} continue to evolve"
        ]
        
        return generic_points[:count]
    
    async def _generate_subsections(self, main_point: str, count: int) -> List[str]:
        """Generate subsections for a main point"""
        
        subsections = []
        for i in range(1, count + 1):
            subsections.append(f"Aspect {i} of {main_point.lower()}")
        
        return subsections