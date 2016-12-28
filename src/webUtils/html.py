from lxml import etree
from lxml.builder import E
import json
from time import strftime
from xml.sax.saxutils import escape


def CLASS(*args):
	return {"class":' '.join(args)}

def buildCards(line_lookup):
	cards = []
	for article in line_lookup:
		title = article.title
		text = article.text
		card = E.div(
			CLASS("card", *[l.replace(" ","-") for l in line_lookup[article]]),
			E.title(title),
			E.div(
				CLASS("card-image waves-effect waves-block waves-light"),
				E.img(
					CLASS("activator"), "",
					src=article.img
				)
			),
			E.div(
				CLASS("card-content"),
				E.span(
					CLASS("card-title activator grey-text text-darken-4"),
					title,
					E("i","more_vert", CLASS("material-icons right"))
				),
				E.p(
					E.a(
						"Read more at "+ article.feed_name,
						href=article.url
					)
				)
			),
			E.div(
				CLASS("card-reveal"),
				E.span(
					CLASS("card-title activator grey-text text-darken-4"),
					title,
					E("i","close",CLASS("material-icons right"))
				),
				article.html
			)
		)
		cards.append(card)
	return cards


def writePage(nodes, links, line_lookup):
	with open("webUtils/newsgraph.css", "r") as css:
		default_css = css.read()
	with open("webUtils/newsgraph.js", "r") as js:
		default_js = js.read()
		default_js = default_js.replace("NG-NODES", json.dumps(nodes))
		default_js = default_js.replace("NG-LINKS", json.dumps(links))

	page = (
		E.html(
			E.head(
				E.title("NewsGraph"),
				E.link(
					href="https://cdnjs.cloudflare.com/ajax/libs/materialize/0.97.6/css/materialize.min.css",
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
					*buildCards(line_lookup),
					id="cards"
				), 
				E("script", "NG-JS")
			)
		)
	)

	with open("ng.html", "w") as ng:
		ng.write(etree.tostring(page, pretty_print=True).replace("NG-JS", default_js))
	#print(etree.tostring(page, pretty_print=True))
