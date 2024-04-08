# Project Overview
The Army relies on memorandums to operate. The guidelines for these memorandums are fairly simple, but they can be tedious to implement in Microsoft Word, which sucks, or is susceptible to fat finger errors. I am tired of both making mistakes and noticing the mistakes of others. For a document standard that is so rigid, WYSIWYG is not the solution.

While some brilliant soul has already created a [latex class for Army memos](https://github.com/glallen01/army-memorandum-class), latex is intimidating and inaccessible to the average soldier. By writing a *hopefully* easy-to-use markdown-inspired language, I hope to bring the reliability of latex to a less technical audience. The website can be found at [http://www.armymemomaker.com]. 

The goal of this project is two-fold:

1. Develop a simple, intuitive markdown-like language for Army memos. Then, a parser will process, proofread, and use latex to output a PDF in accordance with AR 25-50 Managing Correspondance.
2. Create a website where soldiers can upload/type memos and the server will compile the latex and make the memo available for download.

## Features
- Web server where you can create and download memos
- ~~Custom syntax highlighting and code editor~~ (blocked by DODIN-A, no javascript-based code editor will work)
- Supports multiple features, like text styling, basic tables, classifications, enclosures, etc.
- Easily recover last session document


### TODO 
- [x] Containerize and get off Heroku (save $$$, get actual on-demand pricing v. Heroku nonsense)
- [x] Support embedded tables (sort of works, they're not pretty though)
- [x] Add user database so organizational information will auto-fill (could use cookies or account login, maybe save previous documents...)
- [x] Add SSL support
- [ ] Optimize latex compilation so it doesn't take so dang long
- [ ] Allow form-based submission alternatives.
- [ ] Upload list of files (if you have a bunch of command memos to generate, for example) and receive list of PDFs.
  
### Stack / How to Run
This web app is fully containerized. I use ```docker-compose``` to run three containers: 
1. A simple ```flask``` app served via ```gunicorn```
2. A ```celery``` worker
3. A ```redis``` server for task scheduling with ```celery```

The ```celery``` worker handles the time-intensive ```lualatex``` compilation. Then I upload the generated pdf to an AWS S3 bucket and serve it to the client.

## Army Markdown Template
I arrived on the following markdown language design, where each document starts with the basic config signified by ALLCAPS_VARIABLE=example text. It's not particularly elegant, as it's sensitive to both whitespace and the unescape "=" delimiter. 

The memo is whatever follows the SUBJECT= parameter. Each paragraph is signified by a "-". It supports Github-like markdown for italicized, bolded, and highlighted text.

```
ORGANIZATION_NAME=4th Engineer Battalion
ORGANIZATION_STREET_ADDRESS=588 Wetzel Road
ORGANIZATION_CITY_STATE_ZIP=Colorado Springs, CO 80904

OFFICE_SYMBOL=ABC-DEF-GH
AUTHOR=Joseph C. Schlessinger
RANK=1LT
BRANCH=EN
TITLE=Platoon Leader

MEMO_TYPE=MEMORANDUM FOR RECORD

SUBJECT=Template for Army markdown

- This memo is a demonstration of what.

- This item contains sub items.
    - A subitem is created by simply indenting 4 spaces beyond the previous level.
    - A second subitem within the same item point.
        - Here is a sub sub item

- Back to the original level.

- Point of contact is the undersigned blah blah blah.
```
