# Recommender System 2019 Competition

## Code Notation

 - Java-style (i.e. FirstLetterUppercase) notation for Class file and Class name
 - Python-style (i.e. under_score) notation for function definition and function-only filename (e.g. helper files)
 - Python-style for variable names
 - Jupyter notebooks name format should be: <code>dev_name_notebook_name_only_lowercase.ipynb</code>
 - Packages and directories names should be written only lowercase

## Requirements

 - Python 3.6 virtual environment

## Installation
1. <code>pip install -r requirements_dev.txt</code>
2. Follow the guide on how to compile all cython files in <a href="https://github.com/MaurizioFD/RecSys_Course_2018">RecSys Course 2018 GitHub Project </a>

## Jupyter Notebooks
All notebooks has as a root folder <code>notebooks/</code>

### Versioning Notebooks
In order to versioning notebooks, use <a href="https://github.com/mwouts/jupytext">jupytext</a> which is a library of
commands written in python to convert notebooks into pure python files.
For pairing a notebook, after having installed jupytext, it is possible to do it by
<pre><code>jupytext --set-formats ipynb,py notebook.ipynb</code></pre>
Then, it is possible to sync (i.e. update python file) with
<pre><code>jupytext --sync notebook.ipynb</code></pre>

### Convert Notebook to HTML
To convert a notebook into HTML, just run the following command line
<pre><code>jupyter nbconvert --to html notebook.ipynb</code></pre>
Remember to move the html file into the **report** section folder
