"""Abstract interface for document loader implementations."""
from bs4 import BeautifulSoup

from core.rag.extractor.extractor_base import BaseExtractor
from core.rag.models.document import Document
from typing import Optional
from bs4 import BeautifulSoup
class HtmlExtractor(BaseExtractor):

    """
    Load html files.


    Args:
        file_path: Path to the file to load.
    """

    def __init__(
        self,
        file_path: str
    ):
        """Initialize with file path."""
        self._file_path = file_path

    def extract(self) -> list[Document]:
        text, url_value = self._load_as_text()
        metadata = {"url": ""}
        if url_value is not None and url_value.strip():
              metadata = {"url": url_value}
        return [Document(page_content=text, metadata=metadata)]

    def _load_as_text(self) ->tuple[str, str]:
        with open(self._file_path, "rb") as fp:
            soup = BeautifulSoup(fp, 'html.parser')
            metadata_tag = soup.find('metadata')
            url_tag=None
            url_value=""
            if metadata_tag:
                url_tag = metadata_tag.find('url')
            if url_tag:
                url_value = url_tag.string
            else:
                url_value=""
            # 删除 metadata 标签
            if metadata_tag:
                metadata_tag.decompose()
            text = soup.get_text()
            text = text.strip() if text else ''

        return text,url_value