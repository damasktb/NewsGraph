var width = window.innerWidth * 0.7, 
    height = window.innerHeight-60;

var energy;
var unplaced = 0;

var color = color = d3.scale.ordinal()
            .domain(50)
            .range(["#1596ff", "#ff6401", "#fd85b0", "#fef302", "#03aa4a", "#38d8ce", "#e0d8ff", "#d485ff", "#21fed9", "#a78f7b", "#fe906e", "#fe45c1", "#7c9f10", "#6ea87a", "#0afe7a", "#a6f9fd", "#af83c1", "#ffa103", "#ff576d", "#66c1fe", "#97f1a0", "#3fc104", "#febbc0", "#8494ad", "#a1fe04", "#e0bb10", "#ccd0c7", "#da6bc0", "#b4d404", "#dc7a28", "#09fba9", "#08bf8a", "#ffbcfa"]);

var radius = d3.scale.sqrt().range([0, 6]);

var svg = d3.select("body")
    .append("svg")
    .attr("id", "graph")
    .attr("width", width)
    .attr("height", height);

var article_container = d3.select("body")
    .append("div")
    .attr("id", "article-container")
    .attr("width", window.innerWidth * 0.3)
    .attr("height", height);

var force = d3.layout.force()
    .size([width, height-60])
    .charge(
      function(d){
        return -200*(d.weight); 
    })
    .linkDistance(function(d){
        return 5*(1+Math.max(d.source.lines.length, d.target.lines.length));
    })
    .linkStrength(0.9)
    .friction(0.95)
    .alpha(1);

var metro_lines = NG-METRO-LINES;
var graph = {
    "nodes": NG-NODES ,
    "links": NG-LINKS
};

for (var n=0; n<graph.nodes.length;++n) {
  graph.nodes[n].data.date = new Date(graph.nodes[n].data.date);
}


function isInterchange(d) {
  return d.lines.length > 1;
}

var drawGraph = function (graph) {
    force.nodes(graph.nodes)
        .links(graph.links)
        .on("tick", function() {
          tick();
          energy = Math.log(lineStraightness()-1)/10 + Math.log(octilinearity())/10;
          force.alpha(energy);
        })
        .start();

    var link = svg.selectAll(".link")
        .data(graph.links)
        .enter().append("path")
        .style("stroke", function(d) {
          return color(d.line); 
        })
        .attr("class", function (d) {
          return "link count" + d.count;
        });
        

    var node = svg.selectAll(".node")
        .data(graph.nodes)
        .enter().append("g")
        .attr("class", "node")
        .on("click", function(d){
          // Reset all the circles
          var nodes = d3.selectAll(".node");
          nodes.each(function(d) { 
            d3.select(this).select("circle").transition()
              .duration(250)
              .style("fill", isInterchange(d) ? "white" : color(d.lines[0]))
          });
          d3.select(this).select("circle").transition()
            .duration(250)
            .style("fill", "black");
          showArticle(this.__data__.data);
        })
        .call(force.drag);

    node.append("title")
    .text(function(d) { return d.name; });

    node.append("circle")
        .attr("r", function (d) {
          return isInterchange(d)? radius(4): radius(1);
        })
    .style("stroke", function (d) {
        return isInterchange(d) ? "black" : color(d.lines[0]);
    })
    .style("fill", function (d) {
        return isInterchange(d) ? "white" : color(d.lines[0]);
    });

    function tick() {
        function multiTranslate(targetDistance, point0, point1) {
            var x1_x0 = point1.x - point0.x,
                y1_y0 = point1.y - point0.y,
                x2_x0, y2_y0;
            if (y1_y0 === 0) {
                x2_x0 = 0;
                y2_y0 = targetDistance;
            } else {
                var angle = Math.atan((x1_x0) / (y1_y0));
                x2_x0 = -targetDistance * Math.cos(angle);
                y2_y0 = targetDistance * Math.sin(angle);
            }
            return {dx: x2_x0, dy: y2_y0};
        }
        link.attr("d", function (d) {
            var x1 = d.source.x,
                y1 = d.source.y,
                x2 = d.target.x,
                y2 = d.target.y,
                dx = x2 - x1,
                dy = y2 - y1,
                dr = 0;
                var offset = multiTranslate((d.count-1)*7, d.source, d.target);
                x1 += offset.dx;
                x2 += offset.dx;
                y1 += offset.dy;
                y2 += offset.dy;

            return "M" + x1 + "," + y1 + "A" + dr + "," + dr + " 0 0,1 " + x2 + "," + y2;
        });

        node.attr("transform", function (d) {
            return "translate(" + d.x + "," + d.y + ")";
        });

        node.attr("cx", function(d) { return d.x = Math.max(10, Math.min(width-10, d.x)); }) 
            .attr("cy", function(d) { return d.y = Math.max(10, Math.min(height-10, d.y)); });

        var key = svg.selectAll(".key")
            .data(color.domain())
            .enter().append("g")
            .attr("class", "key")
            .attr("transform", function(d, i) { return "translate(0," + i * 25 + ")"; });

        key.append("rect")
            .attr("x", 20)
            .attr("y", 20)
            .attr("width", 50)
            .attr("height", 10)
            .attr("line", function(d) {return d;})
            .style("fill", color)
            .on('click', function(d) {isolateLine(d)});

        key.append("text")
            .attr("x", 75)
            .attr("y", 10)
            .attr("dy", 20)
            .text(function(d) { return d; });
    }
};

var iso_toggle = 0;

function isolateLine(d) {
var node = d3.selectAll(".node");
var link = d3.selectAll(".link");
if (iso_toggle==0) {
  var edges = metro_lines[d];
  var sz = Math.max(width, height);
  var l = {start: sz/10, end: sz-(sz/10), step: (sz*0.8)/(edges.length)};
  node.transition().style("opacity", function (o) {
      return o.lines.indexOf(d) > -1 ? 1 : 0;
  }).attr("px", function(o, i) {
    console.log(o.x, o.lines.indexOf(d) > -1 ? l.start+i*l.step : null);
    return o.lines.indexOf(d) > -1 ? l.start+i*l.step : o.x;
    }).attr("py", function(o) {
    return o.lines.indexOf(d) > -1 ? Math.min(width, height)/2 : o.y;
    })
    .duration(800);
  link.transition().duration(800).style("opacity", function (o) {
      return o.line == d? 1 : 0;
  });


  
  
    
  // var first = graph.nodes[edges[0][0]];
  // first.px = width > height? l.start : width/2;
  // first.py = width > height? height/2: l.start;
  // first.old = {x: first.x, y: first.y};
  // for (var s=0; s < edges.length; s++) {
  //   let next = graph.nodes[edges[s][1]];
  //   next.px = width > height? l.start + (s+1)*l.step : width/2;
  //   next.py = width > height? height/2 : l.start + (s+1)*l.step;
  //   next.old = {x: next.x, y: next.y};
  // }
} else {
  node.transition().duration(800).style("opacity", 1);
  link.transition().duration(800).style("opacity", 1);
  for (var n=0; n<graph.nodes.length; n++) {
    if (graph.nodes[n].old) {
      graph.nodes[n].px = graph.nodes[n].old.x;
      graph.nodes[n].py = graph.nodes[n].old.y;
    }
  }
}
force.start();
force.tick();
force.stop();
iso_toggle = 1-iso_toggle;
}

function move(time) {
  for (var n=0; n<graph.nodes.length; n++) {
    graph.nodes[n].fixed = false;
  }
  force.start();
  window.setTimeout(function(){
  // Use the force, Luke
    for (var n=0; n<graph.nodes.length; n++) {
      graph.nodes[n].fixed = true;
    }
  }, time);
};

function linelength(p1, p2){
return Math.sqrt(Math.pow(p1.x-p2.x,2) + Math.pow(p1.y-p2.y,2));
}

function getMetrics(graph, spacing) {
var metrics = { x_min: width, x_max: 0,
                y_min: height, y_max: 0,
                x_avg: 0, y_avg: 0,
                v_scale: 0, h_scale: 0 };

metrics.x_min = Math.min.apply(null, graph.nodes.map(function(d) {return d.px;}));
metrics.y_min = Math.min.apply(null, graph.nodes.map(function(d) {return d.py;}));
metrics.x_max = Math.max.apply(null, graph.nodes.map(function(d) {return d.px;}));
metrics.y_max = Math.max.apply(null, graph.nodes.map(function(d) {return d.py;}));

metrics.x_avg = (metrics.x_min+metrics.x_max)/2.0;
metrics.y_avg = (metrics.y_min+metrics.y_max)/2.0;

metrics.v_scale = Math.abs(metrics.y_max - metrics.y_min)/(height-2*spacing);
metrics.h_scale = Math.abs(metrics.x_max - metrics.x_min)/(height-2*spacing); // Deliberate
metrics.x_move = metrics.x_avg-width/2.0;
metrics.y_move = metrics.y_avg-height/2.0;

return metrics;
}

function snap(){
var spacing = height/10;

force.stop();
for (var n=0; n<graph.nodes.length; n++) {
  let node = graph.nodes[n];
  c = { x: Math.ceil(node.x/spacing) * spacing,
        y: Math.ceil(node.y/spacing) * spacing};
  node.x, node.px = c.x, c.x;
  node.y, node.py = c.y, c.y;
}

var metrics = getMetrics(graph, spacing);

var taken = {}
for (var n=0; n<graph.nodes.length; n++) {
  let node = graph.nodes[n];
  node.x = (node.x-metrics.x_avg) * (1.0/metrics.h_scale);
  node.y = (node.y-metrics.y_avg) * (1.0/metrics.v_scale);

  c = { x: Math.ceil((node.x+metrics.x_avg)/spacing) * spacing,
        y: Math.ceil((node.y+metrics.y_avg)/spacing) * spacing};

  if (!taken[JSON.stringify(c)]) {
    taken[JSON.stringify(c)] = true;
    node.x, node.px = c.x, c.x;
    node.y, node.py = c.y, c.y;
    node.placed = true;
  }
}

for (var line in metro_lines) {
  line = metro_lines[line];
  for (var s=1; s<line.length; s++) {
    let a=graph.nodes[line[s-1][0]];
    let b=graph.nodes[line[s][0]];
    let c=graph.nodes[line[s][1]];
    let candidate = {x:(a.px+c.px)/2, y:(a.py+c.py)/2};

    if (octilinear(a, c) && !taken[JSON.stringify(candidate)] && b.weight==2)  {
      taken[JSON.stringify(b)] = false;
      taken[JSON.stringify(candidate)] = true;
      b.x, b.px = candidate.x, candidate.x;
      b.y, b.py = candidate.y, candidate.y;
      a.placed = true;
      b.placed = true;
      c.placed = true;
    }
  }
}

for (var line in metro_lines) {
  line = metro_lines[line];
  for (var s=1; s<line.length; s++) {
    let a=graph.nodes[line[s-1][0]];
    let b=graph.nodes[line[s][0]];
    let c=graph.nodes[line[s][1]];
    let candidate = {x:(a.px+c.px)/2, y:(a.py+c.py)/2}; 

    if (!b.placed && !taken[JSON.stringify(candidate)])  {
      taken[JSON.stringify(b)] = false;
      taken[JSON.stringify(candidate)] = true;
      b.x, b.px = candidate.x, candidate.x;
      b.y, b.py = candidate.y, candidate.y;
      a.placed = true;
      b.placed = true;
      c.placed = true;
    }
  }
}

var metrics = getMetrics(graph, spacing);

for (var n=0; n<graph.nodes.length; n++) {
  let node = graph.nodes[n];
  node.px = (node.px*metrics.v_scale) - metrics.x_move;
  node.py = (node.py*metrics.h_scale) - metrics.y_move;

  node.x = node.px;
  node.y = node.py;
}

for (var n=0; n<graph.nodes.length; n++) {
  unplaced += graph.nodes[n].placed? 0:1;
  // if (!graph.nodes[n].placed) {
  //   console.log(graph.nodes[n]);
  // }
}
force.start();
console.log(unplaced);
}

function octilinear(p1, p2) {
if (p1.py == p2.py) {
  return true;
} else if (p1.px == p2.px) {
  return true;
} else {
  return Math.abs((p2.px-p1.px)/(p2.py-p1.py))==1;
}
}


// This will fail if any link has the same source and target co-ordinates
var octilinearity = function(){
var total = 0;
for (var n=0; n<graph.links.length; n++) {
    let s = graph.links[n].source;
    let t = graph.links[n].target;
    let theta = 4*Math.atan(Math.abs((s.py-t.py)/(s.px-t.px)));
    total += Math.abs(Math.sin(theta));
  }
return total;
}

// This will fail if basically any points are drawn on top of each other :(
var lineStraightness = function(){
var total = 0;
for (var line in metro_lines) {
  line = metro_lines[line];
  for (var s=0; s<line.length-1; s++) {
    let a = graph.nodes[line[s][0]];
    let b = graph.nodes[line[s+1][0]];
    let c = graph.nodes[line[s+1][1]];
    let v1 = {x:a.px - b.px, y:a.py - b.py};
    let v2 = {x:c.px - b.px, y:c.py - b.py};

    var v1mag = Math.sqrt(v1.x * v1.x + v1.y * v1.y);
    var v2mag =  Math.sqrt(v2.x * v2.x + v2.y * v2.y);
    var v1norm = {x:v1.x / v1mag, y:v1.y / v1mag};
    var v2norm = {x:v2.x / v2mag, y:v2.y / v2mag};
    
    var res = (v1norm.x * v2norm.x + v1norm.y * v2norm.y);
    // Make sure we don't NaN on e.g. acos(1.0000000000002)
    res = Math.round(res * 100) / 100;
    
    var theta = Math.acos(res);
    if (theta > Math.PI/2) {
      // Wrong direction, we want the < 180 degree angle
      theta = Math.PI-theta;
    }
    total+= theta;
  }
}
return total;
}

move(5000);
setTimeout(function(){ snap(); }, 5500);


function showArticle(data) {
  $('#article-container').get(0).innerHTML = data.html;
    //`<h1>${data.title}</h1><h2>${data.date}</h2><img src='${data.img}'/>`
}

$('#graphPane').click(function() {
  $("#cards").hide();
  $('#feedPane').removeClass("active");
  $("#graph").show();
  $("#article-container").show();
  $('#graphPane').addClass("active");
});

$("#feedPane").click(function() {
  $("#graph").hide();
  $("#article-container").hide();
  $('#graphPane').removeClass("active");
  $("#cards").show();
  $('#feedPane').addClass("active");
});

 $("#graphPane").trigger("click");
drawGraph(graph);