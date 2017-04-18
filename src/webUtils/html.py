# -*- coding: latin-1 -*-
from json import dumps
from lxml import etree
from lxml.builder import E
from time import mktime, strftime
from datetime import datetime
from xml.sax.saxutils import escape

class Libraries:
  MATERIALIZE = "https://cdnjs.cloudflare.com/ajax/libs/"+ \
  "materialize/0.98.0/css/materialize.min.css"
  MATERIAL_ICONS = \
  "https://fonts.googleapis.com/icon?family=Material+Icons"
  
  D3 = "http://d3js.org/d3.v2.min.js?2.9.6"
  JQUERY = "https://code.jquery.com/jquery-3.1.1.min.js"
  JQUERY_UI = "http://code.jquery.com/ui/1.11.0/jquery-ui.min.js"

def CLASS(*args):
  return {"class":' '.join(args)}

def buildCards(articles):
  """
  Build the "feed" pane of the web view
  """
  cards = []
  for article in articles:
    card = E.div(
      CLASS("card horizontal", 
        *[l.replace(" ","-") for l in article.metro_lines]
      ),
      E.div(
        CLASS("card-image"),
        E.img(src=article.img)
      ),
      E.div(
        CLASS("card-stacked"),
        E.div(
          CLASS("card-content"),
          E.h4(article.title),
          E.p(article.summary)
        ),
        E.div(
          CLASS("card-action"),
          strftime("%c", article.publish_date),
          " - ",
          E.a(
            "Read more at "+ article.feed_name,
            href="/#"#article.url
          )
        )
      )
    )
    cards.append(card)
  return cards


def writePage(nodes, links, articles, metro_lines):
  """
  Generate the page, insert our station data JSON at the placeholders.
  """
  with open("webUtils/newsgraph.css", "r") as css:
    default_css = css.read()
  with open("webUtils/newsgraph.js", "r") as js:
    default_js = js.read()
    default_js = default_js.replace("NG-NODES", dumps(nodes))
    default_js = default_js.replace("NG-LINKS", dumps(links))
    default_js = default_js.replace("NG-METRO-LINES", dumps(metro_lines))

  page = (
    E.html(
      E.head(
        E.title("NewsGraph"),
        E.link(
          href=Libraries.MATERIALIZE,
          rel="stylesheet",
          type="text/css"
        ),
        E.link(
          href=Libraries.MATERIAL_ICONS,
          rel="stylesheet",
          type="text/css"
        ),
        E("script", "", src=Libraries.D3),
        E("script", "", src=Libraries.JQUERY),
        E("script", "", src=Libraries.JQUERY_UI),
        E.style(default_css)
      ),
      E.body(
        E("nav",
          E.div(
            CLASS("nav-wrapper yellow darken-3"),
            E.span(CLASS("brand-logo center"), "NewsGraph"),
            E.ul(
              CLASS("right hide-on-med-and-down"),
              E.li(E.a("Graph", href="#"), 
                CLASS("active"), id="graphPane"
              ),
              E.li(E.a("Feed", href="#"), id="feedPane"),
              id="nav-mobile"
            )
          )
        ),
        E.div(
          *buildCards(articles),
          id="cards"
        ), 
        E("script", "NG-JS")
      )
    )
  )

  with open("ng.html", "w") as ng:
    ng.write(etree.tostring(
      page, 
      pretty_print=True, 
      encoding="ISO-8859-1", 
      doctype="<!DOCTYPE html>").replace("NG-JS", default_js
    ))