import pytest
from aiofetch.utils import ContentParser


class TestContentParser:
    @pytest.fixture
    def complex_html(self):
        return """
        <html>
            <body>
                <a href="/relative/path">Relative Link</a>
                <a href="https://absolute.com/path">Absolute Link</a>
                <a href="#local">Local Link</a>
                <a href="javascript:void(0)">JavaScript Link</a>
                <a href="" title="Empty Link">Empty Link</a>
                <img src="/img1.jpg" alt="Image 1" title="Title 1">
                <img src="https://example.com/img2.jpg">
                <img src="" alt="Empty Image">
            </body>
        </html>
        """

    def test_extract_links_relative_absolute(self, complex_html):
        parser = ContentParser()
        base_url = "https://example.com"
        links = parser.extract_links(complex_html, base_url=base_url)

        assert len(links) == 3  # Should exclude javascript and empty links
        assert any(link["url"] == f"{base_url}/relative/path" for link in links)
        assert any(link["url"] == "https://absolute.com/path" for link in links)

    def test_extract_links_no_base_url(self, complex_html):
        parser = ContentParser()
        links = parser.extract_links(complex_html)

        assert any(link["url"] == "/relative/path" for link in links)
        assert any(link["url"] == "https://absolute.com/path" for link in links)

    def test_extract_images_with_missing_attributes(self, complex_html):
        parser = ContentParser()
        images = parser.extract_images(complex_html, base_url="https://example.com")

        assert len(images) == 2  # Should exclude empty src
        assert any(img["alt"] == "" for img in images)  # Missing alt
        assert any(img["title"] == "" for img in images)  # Missing title

    @pytest.mark.parametrize("html,expected_count", [
        ("<html></html>", 0),
        ("<img src='test.jpg'>", 1),
        ("Invalid HTML", 0),
        ("", 0),
    ])
    def test_extract_images_edge_cases(self, html, expected_count):
        parser = ContentParser()
        images = parser.extract_images(html)
        assert len(images) == expected_count
