"""Regression checks for asynchronous fixture record discovery."""

from utils.waits import table_row_exists


def test_waits_for_delayed_row(page):
    page.set_content('<table><tbody></tbody></table>')
    page.evaluate("""() => setTimeout(() => {
        document.querySelector('tbody').innerHTML =
            '<tr><td>Material_9707</td></tr>';
    }, 150)""")

    assert table_row_exists(page, 'Material_9707', timeout=2000)


def test_does_not_match_name_prefix(page):
    page.set_content('<table><tr><td>Material_97070</td></tr></table>')

    assert not table_row_exists(page, 'Material_9707', timeout=200)


def test_returns_false_for_missing_row(page):
    page.set_content('<table><tbody></tbody></table>')

    assert not table_row_exists(page, 'Material_9707', timeout=200)
