from typing import List, Dict

class InspirationBlender:
    """
    Blends multiple website inspirations into a unified, unique site structure/content.
    """
    def __init__(self):
        pass

    def blend(self, inspirations: List[Dict], prompt: str) -> Dict:
        """
        Given a list of inspirations and the user prompt, returns a blended site structure/content.
        """
        # Simple blending: concatenate navs, merge main content, use prompt for customization
        navs = [insp['nav'] for insp in inspirations if insp.get('nav')]
        mains = [insp['main'] for insp in inspirations if insp.get('main')]
        title = f"{prompt.title()} | Inspired Site"
        blended_nav = ' | '.join(navs)
        blended_main = '\n---\n'.join(mains)
        return {
            'title': title,
            'nav': blended_nav,
            'main': blended_main,
            'prompt': prompt,
        }
