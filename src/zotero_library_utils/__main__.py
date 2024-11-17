# def main():    
#     pass

# if __name__ == '__main__':
#     main()

import sqlite3

from Counts.counts import count_items_by_author, count_num_distinct_authors, count_authors_per_item
from Items.get_all_items import get_all_items
from Visualizations.pie_chart import pie_chart

db = "/Users/mitchelltillman/Zotero/zotero.sqlite"
conn = sqlite3.connect(db)
item_ids = get_all_items(conn)
authors_count = count_num_distinct_authors(item_ids, conn)
counts = count_items_by_author(item_ids, conn)
title_str1 = "Item Count Per Author"
# counts = count_authors_per_item(item_ids, conn)
# title_str1 = "Number of Authors Per Item"
pie_chart(counts, num_slices=20, title_str=title_str1, sort_by="values")
# print(counts)

# from Parse_PDFs.pdf2md import pdf2md
# from Parse_PDFs.extract_references import get_references_section

# file_path = "/Users/mitchelltillman/Zotero/storage/2AQ36IHF/McGinnis and Perkins - 2012 - A Highly Miniaturized, Wireless Inertial Measureme.pdf"
# md_text = pdf2md(file_path)
# refs_section = get_references_section(md_text)
# print(refs_section)