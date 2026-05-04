import importlib

class TemplateParser:
    """
    Template Parser for handling RAG prompts dynamically across languages.
    """
    def __init__(self, language: str = "en"):
        self.language = language
        self.locales_cache = {}
        self.set_language(language)

    def set_language(self, language: str):
        self.language = language
        if language not in self.locales_cache:
            try:
                # Dynamically load the locale file: stores.llm.tempelate.locales.<lang>.rag
                module_name = f"stores.llm.tempelate.locales.{self.language}.rag"
                self.locales_cache[self.language] = importlib.import_module(module_name)
            except ImportError as e:
                print(f"Error loading locale '{self.language}': {e}")
                # Fallback to english
                if language != "en":
                    self.set_language("en")

    def get(self, template_type: str, **kwargs) -> str:
        """
        Get a specific prompt template and format it with provided variables.
        
        Args:
            template_type: 'system_prompt', 'document_prompt', or 'footer_prompt'
            **kwargs: variables to format the string with.
        """
        module = self.locales_cache.get(self.language)
        if not module:
            return ""

        template = getattr(module, template_type, "")
        if template and kwargs:
            try:
                # Format string using safely passed variables
                return template.format(**kwargs)
            except KeyError as e:
                print(f"Missing formatting key for template {template_type}: {e}")
                return template
        return template
