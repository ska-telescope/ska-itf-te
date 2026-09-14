"""."""

from lxml import etree

from .items import XRayTest


class XHTMLTable:
    """_summary_."""

    table_id = "resultsTable"

    def __init__(self, collection: list[XRayTest]) -> None:
        """_summary_.

        :param collection: _description_
        :type collection: list[Scenario]
        """
        self._collection = collection

    @staticmethod
    def _list(the_list: list[str]):
        if the_list:
            list_items = ", ".join([f"<li>{value}</li>" for value in the_list])
            return f"<ol>{list_items}</ol>"
        return " "

    def _render_row(self, test: XRayTest) -> str:
        return (
            f"<tr>"
            f"<td>{test.xray_id}</td>"
            f"<td>{test.path}</td>"
            f"<td>{test.result}</td>"
            f"<td>{self._list(test.requirements_with_link)}</td>"
            "</tr>"
        )

    def _render_heading(self) -> str:
        return (
            "<tr>"
            "<th>Jira Item</th>"
            "<th>Path</th>"
            "<th>Result</th>"
            "<th>Jama Requirement</th>"
            "</tr>"
        )

    def render(self) -> str:
        """_summary_.

        :return: _description_
        """
        rows = "".join([self._render_row(test) for test in self._collection])
        heading = self._render_heading()
        preamble = '<p class="auto-cursor-target"><br/></p>'
        return (
            f'<div class="{self.table_id}">{preamble}<table class="{self.table_id}"'
            f"><tbody>{heading}{rows}</tbody></table></div>"
        )

    def render_as_xhtml_element(self):
        """_summary_.

        :return: _description_
        """
        parser = etree.XMLParser(encoding="utf-8", recover=True)
        data = self.render()
        return etree.fromstring(data, parser=parser)
