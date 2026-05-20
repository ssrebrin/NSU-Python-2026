import unittest
from unittest.mock import patch, Mock
import main as m


def make_response(html: str, status: int = 200) -> Mock:
    mock = Mock()
    mock.status_code = status
    mock.text = html
    return mock


class TestUtils(unittest.TestCase):
    def test_strip_parentheses(self) -> None:
        s = "Hello (world) test"
        self.assertEqual(m.strip_parentheses(s), "Hello  test")

    def test_extract_title(self) -> None:
        url = "https://en.wikipedia.org/wiki/Hello_World"
        self.assertEqual(m.extract_title(url), "Hello World")

    def test_is_philosophy(self) -> None:
        url = "https://en.wikipedia.org/wiki/Philosophy"
        self.assertTrue(m.is_philosophy(url))

        url2 = "https://en.wikipedia.org/wiki/Math"
        self.assertFalse(m.is_philosophy(url2))


# ------------------------
# HTML parsing
# ------------------------


class TestFindFirstLink(unittest.TestCase):
    def test_simple_html(self) -> None:
        html = """
        <div id="mw-content-text">
            <p>
                Some text <a href="/wiki/Test">Test</a>
            </p>
        </div>
        """

        link = m.find_first_link(html)
        self.assertEqual(link, "https://en.wikipedia.org/wiki/Test")

    def test_skip_invalid_links(self) -> None:
        html = """
        <div id="mw-content-text">
            <p>
                <a href="/wiki/Special:Something">Bad</a>
                <a href="/wiki/Good">Good</a>
            </p>
        </div>
        """

        link = m.find_first_link(html)
        self.assertEqual(link, "https://en.wikipedia.org/wiki/Good")

    def test_no_valid_link(self) -> None:
        html = """
        <div id="mw-content-text">
            <p>No links here</p>
        </div>
        """

        self.assertIsNone(m.find_first_link(html))


class TestWikiIterator(unittest.TestCase):
    @patch("main.requests.get")
    @patch("main.time.sleep", return_value=None)
    def test_basic_iteration(self, mock_sleep: Mock, mock_get: Mock) -> None:
        html1 = """
        <div id="mw-content-text">
            <p><a href="/wiki/Page2">Next</a></p>
        </div>
        """

        html2 = """
        <div id="mw-content-text">
            <p><a href="/wiki/Philosophy">Next</a></p>
        </div>
        """

        mock_get.side_effect = [
            make_response(html1),
            make_response(html2),
        ]

        it = m.WikiIterator("https://en.wikipedia.org/wiki/Page1", sleep_time=0)

        pages = list(it)

        self.assertEqual(
            pages,
            [
                "https://en.wikipedia.org/wiki/Page1",
                "https://en.wikipedia.org/wiki/Page2",
            ],
        )

    @patch("main.requests.get")
    @patch("main.time.sleep", return_value=None)
    def test_cycle(self, mock_sleep: Mock, mock_get: Mock) -> None:
        html = """
        <div id="mw-content-text">
            <p><a href="/wiki/Page1">Loop</a></p>
        </div>
        """

        mock_get.return_value = make_response(html)

        it = m.WikiIterator("https://en.wikipedia.org/wiki/Page1", sleep_time=0)

        pages = list(it)

        self.assertEqual(pages, ["https://en.wikipedia.org/wiki/Page1"])

    @patch("main.requests.get")
    @patch("main.time.sleep", return_value=None)
    def test_no_link(self, mock_sleep: Mock, mock_get: Mock) -> None:
        html = """
        <div id="mw-content-text">
            <p>No links</p>
        </div>
        """

        mock_get.return_value = make_response(html)

        it = m.WikiIterator("https://en.wikipedia.org/wiki/Page1", sleep_time=0)

        pages = list(it)

        self.assertEqual(pages, ["https://en.wikipedia.org/wiki/Page1"])

    @patch("main.requests.get")
    @patch("main.time.sleep", return_value=None)
    def test_max_steps(self, mock_sleep: Mock, mock_get: Mock) -> None:
        html = """
        <div id="mw-content-text">
            <p><a href="/wiki/Next">Next</a></p>
        </div>
        """

        mock_get.return_value = make_response(html)

        it = m.WikiIterator(
            "https://en.wikipedia.org/wiki/Page1", sleep_time=0, max_steps=2
        )

        pages = list(it)

        self.assertEqual(len(pages), 2)


if __name__ == "__main__":
    unittest.main()
