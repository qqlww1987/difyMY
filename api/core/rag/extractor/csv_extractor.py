"""Abstract interface for document loader implementations."""
import csv
from io import TextIOWrapper
from typing import Optional

import pandas as pd

from core.rag.extractor.extractor_base import BaseExtractor
from core.rag.extractor.helpers import detect_file_encodings
from core.rag.models.document import Document


class CSVExtractor(BaseExtractor):
    """Load CSV files.


    Args:
        file_path: Path to the file to load.
    """

    def __init__(
            self,
            file_path: str,
            encoding: Optional[str] = None,
            autodetect_encoding: bool = False,
            metadata_columns: list[str] = ["url"],
            source_column: Optional[str] = None,
            csv_args: Optional[dict] = None,
    ):
        """Initialize with file path."""
        self._file_path = file_path
        self._encoding = encoding
        self.metadata_columns = metadata_columns
        self._autodetect_encoding = autodetect_encoding
        self.source_column = source_column
        self.csv_args = csv_args or {}

    # def extract(self) -> list[Document]:
    #     """Load data into document objects."""
    #     docs = []
    #     try:
    #         with open(self._file_path, newline="", encoding=self._encoding) as csvfile:
    #             docs = self._read_from_file(csvfile)
    #     except UnicodeDecodeError as e:
    #         if self._autodetect_encoding:
    #             detected_encodings = detect_file_encodings(self._file_path)
    #             for encoding in detected_encodings:
    #                 try:
    #                     with open(self._file_path, newline="", encoding=encoding.encoding) as csvfile:
    #                         docs = self._read_from_file(csvfile)
    #                     break
    #                 except UnicodeDecodeError:
    #                     continue
    #         else:
    #             raise RuntimeError(f"Error loading {self._file_path}") from e

    #     return docs

    # def _read_from_file(self, csvfile) -> list[Document]:
    #     docs = []
    #     try:
    #         # load csv file into pandas dataframe
    #         df = pd.read_csv(csvfile, error_bad_lines=False, **self.csv_args)

    #         # check source column exists
    #         if self.source_column and self.source_column not in df.columns:
    #             raise ValueError(f"Source column '{self.source_column}' not found in CSV file.")

    #         # create document objects

    #         for i, row in df.iterrows():
    #             content = ";".join(f"{col.strip()}: {str(row[col]).strip()}" for col in df.columns)
    #             source = row[self.source_column] if self.source_column else ''
    #             metadata = {"source": source, "row": i}
    #             doc = Document(page_content=content, metadata=metadata)
    #             docs.append(doc)
    #     except csv.Error as e:
    #         raise e

    #     return docs
    def extract(self) -> list[Document]:
        """Load data into document objects."""
        docs = []
        try:
            with open(self._file_path, newline="", encoding=self._encoding) as csvfile:
                docs = self._read_from_file(csvfile)
        except UnicodeDecodeError as e:
            if self._autodetect_encoding:
                detected_encodings = detect_file_encodings(self._file_path)
                for encoding in detected_encodings:
                    try:
                        with open(self._file_path, newline="", encoding=encoding.encoding) as csvfile:
                            docs = self._read_from_file(csvfile)
                        break
                    except UnicodeDecodeError:
                        continue
            else:
                raise RuntimeError(f"Error loading {self._file_path}") from e
        return docs
    def _read_from_file(self, csvfile) -> list[Document]:
        docs = []

        csv_reader = csv.DictReader(csvfile, **self.csv_args)
        for i, row in enumerate(csv_reader):
            try:
                source = (
                    row[self.source_column]
                    if self.source_column is not None
                    else self._file_path
                )
            except Exception as e:
                print (f"Error reading {self._file_path}",e) 
            except KeyError:
                raise ValueError(
                    f"Source column '{self.source_column}' not found in CSV file."
                )
            content = "\n".join(
                f"{k.strip()}: {v.strip() if v is not None else v}"
                for k, v in row.items()
                if k not in self.metadata_columns
            )

            metadata = {"source": source, "row": i}
            for col in self.metadata_columns:
                try:
                    metadata[col] = row[col]
                except Exception as e:
                    print (f"Error reading {self._file_path}",e)   
                except KeyError:
                    raise ValueError(f"Metadata column '{col}' not found in CSV file.")
            doc = Document(page_content=content, metadata=metadata)
            
            # print("metadata:"+metadata)
            # print("page_content:"+content)
            # print("page_content:"+content+"------metadata:"+metadata)
            docs.append(doc)

        return docs
