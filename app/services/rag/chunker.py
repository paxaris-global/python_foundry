from langchain_text_splitters import RecursiveCharacterTextSplitter


class CodeChunker:
    def __init__(self, chunk_size: int = 1200, chunk_overlap: int = 120):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\nclass ", "\ndef ", "\ninterface ", "\nfunction ", "\n", " "],
        )

    def chunk(self, content: str) -> list[str]:
        return self.splitter.split_text(content)
