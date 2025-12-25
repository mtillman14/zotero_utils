# zotero-utils

This project aims to provide tools to understand the makeup of a Zotero library - entirely locally - by reading from Zotero's SQLite database. This package focuses on providing tools that Zotero itself does not provide.

# Installation
```bash
pip install zotero-utils
```

# Help
Using the magic of [Typer](https://typer.tiangolo.com), you can get help messages for this package using 
```bash
zotero-utils --help
```
And for each command you can also see a help message.
```bash
zotero-utils show-creators-per-item --help
```

# Tools
## Counts
Provides counts of several pieces of metadata:
    
1. Number of articles from each author. Optionally, you can specify the number of bars shown.
```bash
zotero-utils show-items-per-creator --num-groups=20
```
![Number of Articles from Top 20 Authors](docs/show_items_per_creator_bar.png)

You can also choose to visualize this info as a pie chart.
```bash
zotero-utils show-items-per-creator --vis-type pie
```

2. Number of different authors in the database (identified by first and last name)
```bash
zotero-utils count-distinct-authors
```

3. Number of articles with 1-N authors. Optionally, you can specify the number of bars shown.
```bash
zotero-utils show-creators-per-item --num-groups=20
```
![Number of Authors Per Article](docs/show_creators_per_item_bar.png)

You can also choose to visualize this info as a pie chart.
```bash
zotero-utils show-creators-per-item --vis-type pie
```

## Timelines
Visualize when articles were published. By default, details of each publication are shown. Optionally, they can be hidden.
```bash
zotero-utils show-timeline-date-published --no-show-details
```
![Article Publication Timeline](docs/article_publication_timeline.png)

# Contributing
For errors and feature suggestions, please open an issue. Pull requests are also appreciated and will be reviewed ASAP.

# Roadmap
## Reference Graph
I'd like to be able to build a graph of the references between items in the Zotero database. Sticking to the local-first design, this means parsing PDF's for their references, which is a notoriously difficult problem. Any suggestions are welcome, please open an issue!

## Zotero Local API
Apparently, Zotero also supports a [local version](https://github.com/zotero/zotero/blob/dc39ca37566ac379611cad9253d48a054d915e9b/chrome/content/zotero/xpcom/localAPI/server_localAPI.js#L26-L64) of the [web API](https://www.zotero.org/support/dev/web_api/v3/start), and they recommend that applications use that.