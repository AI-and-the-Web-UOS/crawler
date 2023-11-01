# A single-server HTML-page crawler for webpage headings

## Project for AI and the Web

This is a simple web crawler that retrieves H1-headings from all directly or indirectly linked HTML-pages on the same server starting from a single URL.
This project was part of the course "AI and the Web" at _University of Osnabrueck_.
<p align="right">(<a href="#top">back to top</a>)</p>

## 📖 Table of Contents

- [❓ Why?](#-why)
- [✨ Features](#-features)
- [💻 Usage](#-usage)
- [💾 Structure](#-structure)
- [🚫 Limitations](#-limitations)
- [📝 Authors](#-authors)
- [📎 License](#-license)

  <p align="right">(<a href="#top">back to top</a>)</p>

## ❓ Why?

To implement a small-scale search engine the pages from a specified server need to be crawled to provide enable an information search based on semantic similarity of the headings and a relevance scoring.
<p align="right">(<a href="#top">back to top</a>)</p>

## ✨ Features

From a single URL the crawler can extract both headers and all linked URLs on an HTML page and evaluate the linked URLs for validity, response type (only HTML responses are crawled), the domain (all links to different servers are ignored) and whether the URL has been visited and whether it needs to be added to the backlog for crawling.
TO BE IMPLEMENTED: The headers from the webpages are then embedded using the multi-language BERT model _LaBSE_ by Google to compare the semantic similarity of search requests and the headers.
<br/>
<p align="right">(<a href="#top">back to top</a>)</p>

## 💻 Usage

1. Clone the repository or download the code.

```
git clone https://github.com/AI-and-the-Web-UOS/crawler/
cd crawler
```

2. Install the required Python packages.

 ```
pip install -r requirements.txt
```

Or create a conda environment with the required packages.

```
conda  env create -n crawler -f crawler.yaml
conda activate crawler 
```

3. TO BE IMPLEMENTED: Set up your MongoDB server and replace the connection details in the code with your own.

4. Start the crawler.

```
python crawler.py
```

<p align="right">(<a href="#top">back to top</a>)</p>

## 💾 Structure
<!-- Project Structure -->
    .
    ├── README.md
    ├── crawler.yaml
    ├── requirements.txt
    ├── crawler.py                              # The file with the actual crawler
    │── .gitignore
<p align="right">(<a href="#top">back to top</a>)</p>

## 🚫 Limitations

The crawler is limited to same-server webpages and HTML-content. For the search it only retrieves H1-headings within the HTML and not the full page-content.
<p align="right">(<a href="#top">back to top</a>)</p>

## 📝 Authors

[Christine Arnoldt](mailto:carnoldt@uos.de)<br/>
<p align="right">(<a href="#top">back to top</a>)</p>

## 📎 License

Copyright 2023 Christine Arnoldt

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
<p align="right">(<a href="#top">back to top</a>)</p>
