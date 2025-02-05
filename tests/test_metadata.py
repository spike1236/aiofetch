import pytest
from aiofetch.utils import MetadataExtractor, MetadataManager


class TestMetadataExtractor:
    @pytest.fixture
    def metadata_html(self):
        return """
        <html>
            <head>
                <meta name="description" content="Test Description">
                <meta property="og:title" content="OG Title">
            </head>
            <body>
                <h1 class="title">Page Title</h1>
                <div class="author" data-author="John Doe"></div>
            </body>
        </html>
        """

    def test_extract_with_various_selectors(self, metadata_html):
        extractor = MetadataExtractor()
        selectors = {
            "title": "h1.title",
            "description": ('meta[name="description"]', "content"),
            "og_title": ('meta[property="og:title"]', "content"),
            "author": (".author", "data-author")
        }

        metadata = extractor.extract_from_html(metadata_html, selectors)

        assert metadata["title"] == "Page Title"
        assert metadata["description"] == "Test Description"
        assert metadata["og_title"] == "OG Title"
        assert metadata["author"] == "John Doe"

    def test_metadata_cleaning(self):
        extractor = MetadataExtractor(cleaners={
            "title": lambda x: x.upper(),
            "description": lambda x: x.strip()[:50]
        })

        metadata = {
            "title": "test title",
            "description": "  very long description  " * 10
        }

        cleaned = extractor._clean_metadata(metadata)
        assert cleaned["title"] == "TEST TITLE"
        assert len(cleaned["description"]) == 50


class TestMetadataManager:
    def test_find_by_field_multiple_matches(self, temp_dir):
        manager = MetadataManager(temp_dir)
        test_data = [
            {"id": "1", "category": "test", "value": "a"},
            {"id": "2", "category": "test", "value": "b"},
            {"id": "3", "category": "other", "value": "c"}
        ]

        for data in test_data:
            manager.save_metadata(data)

        results = manager.find_by_field("category", "test")
        assert len(results) == 2
        assert all(r["category"] == "test" for r in results)

    def test_load_all_with_invalid_files(self, temp_dir):
        manager = MetadataManager(temp_dir)
        # Create invalid JSON file
        with open(f"{temp_dir}/invalid.json", "w") as f:
            f.write("invalid json")

        manager.load_all()  # Should not raise exception
        assert len(manager.cache) == 0
