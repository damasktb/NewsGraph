from json import dumps
from lxml import etree
from lxml.builder import E
from time import strftime
from xml.sax.saxutils import escape

def CLASS(*args):
	return {"class":' '.join(args)}

def buildCards(articles):
	cards = []
	for article in articles:
		title = article.title
		text = article.text
		card = E.div(
			CLASS("card horizontal", *[l.replace(" ","-") for l in article.metro_lines]),
			E.div(
				CLASS("card-image"),
				E.img(src=article.img)
			),
			E.div(
				CLASS("card-stacked"),
				E.div(
					CLASS("card-content"),
					title,
					E("i","more_vert", CLASS("material-icons right"))
				),
				E.div(
					CLASS("card-action"),
					E.a(
						"Read more at "+ article.feed_name,
						href=article.url
					)
				)
			)
		)
		cards.append(card)
	return cards


def writePage(nodes, links, articles, metro_lines):
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
					href="https://cdnjs.cloudflare.com/ajax/libs/materialize/0.98.0/css/materialize.min.css",
					rel="stylesheet",
					type="text/css"
				),
				E.link(
					href="https://fonts.googleapis.com/icon?family=Material+Icons",
					rel="stylesheet",
					type="text/css"
				),
				E("script", "", src="http://d3js.org/d3.v2.min.js?2.9.6"),
				E("script", "", src="https://code.jquery.com/jquery-3.1.1.min.js"),
				E.style(default_css)
			),
			E.body(
				E("nav",
					E.div(
						CLASS("nav-wrapper yellow darken-3"),
						E.span(CLASS("brand-logo center"), "NewsGraph"),
						E.ul(
							CLASS("right hide-on-med-and-down"),
							E.li(E.a("Graph", href="#"), CLASS("active"), id="graphPane"),
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
		ng.write(etree.tostring(page, pretty_print=True, encoding="UTF-8", doctype="<!DOCTYPE html>").replace("NG-JS", default_js))
