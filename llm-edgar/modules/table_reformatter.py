
from bs4 import BeautifulSoup, NavigableString

class Table_HTML_to_MD:

    def __init__(self, html_format=True):

        self.html_format = html_format

    def table_cleaner(self, table):

        clean_table = self.remove_element(table)
        clean_table = self.remove_table_attributes(clean_table)
        clean_table = self.remove_empty_tags(clean_table)
        clean_table = str(clean_table).replace(u"\xa0", u" ")    

        return clean_table

    def remove_element(self, html_content):
        """ Removes <ix:nonfraction> tags but retains their text content """

        # Find all <ix:nonfraction> elements and replace them with their text content
        for ix_nonfraction in html_content.find_all('ix:nonfraction'):
            ix_nonfraction.replace_with(ix_nonfraction.get_text())

        for ix_nonnumeric in html_content.find_all('ix:nonnumeric'):
            ix_nonnumeric.replace_with(ix_nonnumeric.get_text())

        for spans in html_content.find_all('span'):
            spans.replace_with(spans.get_text())

        for divs in html_content.find_all('div'):
            divs.replace_with(divs.get_text())

        return html_content

    def remove_table_attributes(self, html_content):
        """ Removes all attributes except 'colspan' and 'rowspan' from elements within <table> tags in the given HTML content """

        # Find all <table> elements and iterate over them
        for table in html_content.find_all('table'):
            table.attrs = {}
            # Find all elements within the table
            for tag in table.find_all(True):
                # Keep only colspan and rowspan attributes if they exist
                colspan = tag.get('colspan')
                rowspan = tag.get('rowspan')
                tag.attrs = {}
                if colspan:
                    tag.attrs['colspan'] = colspan
                if rowspan:
                    tag.attrs['rowspan'] = rowspan
                for sp in tag.find_all(True):
                    colspan = sp.get('colspan')
                    rowspan = sp.get('rowspan')
                    sp.attrs = {}
                    if colspan:
                        sp.attrs['colspan'] = colspan
                    if rowspan:
                        sp.attrs['rowspan'] = rowspan

        return html_content

    def remove_empty_tags(self, html_content):
        """ Removes tags from the HTML content that don't contain text, colspan, rowspan, or other attributes """

        for tag in html_content.find_all(True):
            # Check if the tag is empty (no text or attributes like colspan/rowspan)
            if (not tag.attrs) and (not tag.get_text(strip=True)) and (not isinstance(tag, NavigableString)):
                tag.decompose()  # Remove the tag

        return html_content

    def convert_html_to_md(self, html_table):
        table = BeautifulSoup(html_table, 'html.parser')

        # Initialize variables to store table data
        markdown_table = []
        headers = []

        # Process table rows and cells
        for row in table.find_all('tr'):
            cells = [cell.get_text().strip() for cell in row.find_all(['td', 'th'])]
            
            if not headers:
                headers = cells  # Store the first row as headers
            else:
                markdown_table.append(cells)

        # Convert the data to Markdown format
        markdown = '| ' + ' | '.join(headers) + ' |\n'
        markdown += '| ' + ' | '.join(['---'] * len(headers)) + ' |\n'

        for row in markdown_table:
            markdown += '| ' + ' | '.join(row) + ' |\n'

        return markdown

    def convert(self, table_element):

        table = self.table_cleaner(table_element)
        table_md = self.convert_html_to_md(table)

        if self.html_format:
            return table, table_md
        else:
            return table_md