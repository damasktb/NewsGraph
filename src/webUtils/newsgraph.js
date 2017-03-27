var width = window.innerWidth * 0.7, 
    height = window.innerHeight-60;

// How energetically is the map moving into position?
var energy;
// How many stations couldn't be positioned?
var unplaced = 0;
// Position hash
var taken = {};
// Size of one grid square
var spacing = height/8.0;
// Has a metro line on the key been clicked?
var iso_toggle = 0;

// Realistically more colours than we will ever need but I'm hesitant to go for a hard limit
var color = color = d3.scale.ordinal()
  .domain(50)
  .range(["#1596ff", "#ff6401", "#fef302", "#03aa4a", "#38d8ce", "#c38ce2", "#fd85b0", "#a78f7b", "#d8d8d8", "#374a91", "#48e268", "#ffa103", "#ff576d", "#66c1fe", "#97f1a0", "#3fc104", "#febbc0", "#8494ad", "#a1fe04", "#e0bb10"]);

var radius = d3.scale.sqrt().range([0, 6]);

var svg = d3.select("body")
    .append("svg")
    .attr("id", "graph")
    .attr("width", width)
    .attr("height", height)
    .attr("viewBox", "0 0 " + width + " " + height )
    .attr("preserveAspectRatio", "xMidYMid meet")
    .attr("pointer-events", "all");

var article_container = d3.select("body")
    .append("div")
    .attr("id", "article-container")
    .attr("width", window.innerWidth * 0.3)
    .attr("height", height);

var force = d3.layout.force()
    .size([width, height-60])
    .charge(function(d){
        // Nodes with higher weights will repel more strongly
        return d.weight == 1? -300: -500;
    })
    .linkDistance(function(d){
        return height/15;
    })
    .linkStrength(1)
    .friction(0.96)
    .gravity(0.15)
    .alpha(1);

// NG things get regex replaced with actual JSON by the python script, do not remove
var metro_lines = NG-METRO-LINES;
var graph = {
    "nodes": NG-NODES ,
    "links": NG-LINKS
};

// Dates get serialised as plain ints
for (var n=0; n<graph.nodes.length;++n) {
  graph.nodes[n].data.date = new Date(graph.nodes[n].data.date);
}

// Keep a record of which links have multiple metro lines
var multiEdges = {};
for (var l of graph.links) {
  multiEdges[[graph.nodes[l.source], graph.nodes[l.target]]] = 
    Math.max(l.count, 
            multiEdges[[graph.nodes[l.source], 
            graph.nodes[l.target]]]||1);
}

// Helper functions for general station movement, calculation and manipulation
function isInterchange(d) { return d.lines.length > 1; }
function linelength(p1, p2){ return Math.sqrt(Math.pow(p1.x-p2.x,2) + Math.pow(p1.y-p2.y,2)); }
function nan(v) { return v !== v; }
function coordinates(p) { return JSON.stringify({x:Math.round(p.x, 2),y:Math.round(p.y, 2)}); }
function octilinear(p1, p2) {
  if (p1.y == p2.y) {
    return true;
  } else if (p1.x == p2.x) {
    return true;
  } else {
    return Math.abs((p2.x-p1.x)/(p2.y-p1.y)) < 0.1;
  }
}
function gradient(a, b){ return (b.py-a.py)/(b.px-a.px); }
function dist2d(a, b){ return {x: (b.px-a.px), y:(b.py-a.py)}; }

// All the d3 drawing stuff and main loop
var drawGraph = function (graph) {

  force.nodes(graph.nodes)
    .links(graph.links)
    .on("tick", function() {
        // Every tick, change the energy the map has to move relative to how "good"
        // its layout is. Bad graph => high energy to reposition, & vice versa.
        energy = Math.log(octilinearity())/10 + Math.log(lineStraightness())/10;
        force.alpha(energy);
        tick();
    })
    .start();

  // Create the metro line links
  var link = svg.selectAll(".link")
    .data(graph.links)
    .enter().append("path")
    .style("stroke", function(d) {
      return color(d.line); 
    })
    .style("stroke-width", function(d) {
      return 7; // Math.min(10, Math.floor(18/multiEdges[[d.source, d.target]])); 
    })
    .attr("class", function (d) {
      return "link count" + d.count;
    });
  
  // Bind the stations to their data
  var node = svg.selectAll(".node")
    .data(graph.nodes)
    .enter().append("g")
    .attr("class", "node")
    .on("click", function(d){
      // Reset all the circles
      var nodes = d3.selectAll(".node");
      nodes.each(function(d) { 
        d3.select(this).select("circle").transition().duration(250)
          .style("fill", isInterchange(d) ? "white" : color(d.lines[0]))
        });
        d3.select(this).select("circle").transition().duration(250)
        .style("fill", "black")
        // __.data__.data is not a d3 thing (the last .data element is ours and poorly named)
        showArticle(this.__data__.data);
      })
    .call(force.drag);

  // Create the station tooltips
  node.append("title").text(function(d) { return d.name; });

  // Add the station circles and conditionally colour
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

  // Animate.. lots
  function tick() {

    function multiTranslate(targetDistance, point0, point1) {
    // This function is taken from http://webiks.com/d3-js-force-layout-straight-parallel-links/
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

    // Change the angle and position of the links as they move
    link.attr("d", function (d) {
      var x1 = d.source.x, y1 = d.source.y,
          x2 = d.target.x, y2 = d.target.y,
          dr = 0;
          var lw = 7; //Math.min(7, Math.floor(18/multiEdges[[d.source, d.target]]));
          var offset = multiTranslate(d.count==1?0:(Math.floor(d.count/2))*(d.count%2?-lw:lw), d.source, d.target);
          x1 += offset.dx;
          x2 += offset.dx;
          y1 += offset.dy;
          y2 += offset.dy;
      return "M" + x1 + "," + y1 + "A" + dr + "," + dr + " 0 0,1 " + x2 + "," + y2; });

    // Change the position of the nodes as they move & don't let them go off canvas
    node.attr("transform", function (d) { return "translate(" + d.x + "," + d.y + ")"; });
        node
        .attr("cx", function(d) { return d.x = Math.max(10, Math.min(width-10, d.x)); }) 
        .attr("cy", function(d) { return d.y = Math.max(10, Math.min(height-10, d.y)); });

  // Draw the key & bind the click events
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
}

// Toggle the isolation of a single metro line when it's clicked in the key
function isolateLine(d) {
  var node = d3.selectAll(".node");
  var link = d3.selectAll(".link");
  // If no line is selected, isolate the line that was just clicked (d)
  if (iso_toggle==0) {
    var edges = metro_lines[d];
    node.transition().style("fill-opacity", function (o) {
        return o.lines.indexOf(d) > -1 || isInterchange(o)? 1 : 0.1;
    }).style("stroke-opacity", function (o) {
        return o.lines.indexOf(d) > -1 ? 1 : 0.05;
    }).duration(700);
    link.transition().style("opacity", function (o) {
        return o.line == d? 1 : 0.1;
    }).duration(700);
  } else { // Reset everything
    node.transition().duration(700).style("fill-opacity", 1).style("stroke-opacity", 1);
    link.transition().duration(700).style("opacity", 1);
  }
  force.start();
  force.tick(); // All the nodes are fixed so without calling tick(), start() won't work
  force.stop();
  iso_toggle = 1-iso_toggle;
}

// Let the nodes move around a bit and then forceably pause them
// To-do: polling until octilinearity/LS are suitably low, then doing force.alpha(0) breaks things
// but until then we have to have a hard time limit which performs badly sometimes
function move(time) {
  for (var n=0; n<graph.nodes.length; n++) {
    graph.nodes[n].fixed = false;
  }
  force.start();
  window.setTimeout(function(){
  // Wait some completely arbitraty amount of time before 'pausing'
    force.alpha(0);
    for (var n=0; n<graph.nodes.length; n++) {
      graph.nodes[n].fixed = true;
    }
  }, time);
};

// Still not sure whether it's correct to use .x or .px here, like, at all.
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
  metrics.x_move = (metrics.x_min*metrics.v_scale)/2.0;
  metrics.y_move = (metrics.y_min*metrics.h_scale)/2.0;

  return metrics;
}

function exportPositions() {
  positions = [];
  for (var n=0; n<graph.nodes.length; n++) {
    positions[n] = {"x": graph.nodes[n].x, "y": graph.nodes[n].y};
  }
  return JSON.stringify(positions);
}

function importPositions(positions) {
  for (var n=0; n<graph.nodes.length; n++) {
    graph.nodes[n].x = positions[n].x; graph.nodes[n].px = positions[n].x;
    graph.nodes[n].y = positions[n].y + 10; graph.nodes[n].py = positions[n].y + 10;
  }
  force.start();
  force.tick();
  force.stop();
}

function octilineariseLine(li, begin, end, dir) {
  let l = metro_lines[li];
  let line = {x: end.px-begin.px, y: end.py-begin.py};
  let theta = Math.atan(line.y/line.x);
  let nearest = Math.ceil(theta/(Math.PI/4)) * (Math.PI/4);
  if (dir == 1) { // line coming inwards, move 'begin'
    if (Math.round(Math.abs(nearest), 2) == 2 || nan(Math.tan(nearest))) {
      begin.py += linelength(begin, end);
    } else {
      begin.py += line.x * (Math.tan(nearest) - Math.tan(theta));
    }
  } else { // line going outwards, move 'end'
    if (Math.round(Math.abs(nearest), 2) == 2 || nan(Math.tan(nearest))) {
      end.py += linelength(begin, end);
    } else {
      end.py += line.x * (Math.tan(nearest) - Math.tan(theta));
    }
  }
  return {b:begin, e:end};
}

// start and stop are inclusive
function spaceAlongLine(l, start, stop, dir) {
  for (var n=0; n<graph.nodes.length; n++) {
    graph.nodes[n].px = graph.nodes[n].x;
    graph.nodes[n].py = graph.nodes[n].y;
  }
  var line = metro_lines[l];
  let real_begin = start==0? graph.nodes[line[0][0]]: graph.nodes[line[start-1][1]];
  let real_end = graph.nodes[line[stop-1][1]];
  oct = octilineariseLine(l, real_begin, real_end, dir);
  let begin = oct.b;
  let end = oct.e;
  
  let delta = dist2d(begin, end);
  delta.x = Math.ceil(delta.x/(stop-start+1));
  delta.x = (Math.abs(3*delta.x) < spacing)? delta.x*2: (Math.abs(delta.x)>spacing)? delta.x/1.5: delta.x;
  delta.y = Math.ceil(delta.y/(stop-start));
  delta.y = (Math.abs(3*delta.y) < spacing)? delta.y*2: (Math.abs(delta.y)>spacing)? delta.y/1.5: delta.y;

  for (var s=start; s<=stop; s++) {
    let station = s==0? graph.nodes[line[0][0]]: graph.nodes[line[s-1][1]];
    station.x = begin.px + (s-start)*delta.x;
    station.y = begin.py + (s-start)*delta.y;
    station.px = station.x;
    station.py = station.y;
  }
}

// Snap nodes to the grid so that hopefully most of them are drawn octilinearly
// in a discrete point space then do some line straightening and hope for the best
function snap(){
  force.stop();
  var metrics = getMetrics(graph, spacing);

  // This is the snap to grid part, we don't care about collisions yet so
  // don't mark anything as placed or unplaced
  for (var n=0; n<graph.nodes.length; n++) {
    let node = graph.nodes[n];
    node.x = (node.x/metrics.h_scale);
    node.y = (node.y/metrics.v_scale);
    c = { x: Math.ceil(node.x/spacing) * spacing,
          y: Math.ceil(node.y/spacing) * spacing};
    node.x = c.x; node.px = c.x;
    node.y = c.y; node.py = c.y;
  }

  metrics = getMetrics(graph, spacing);

  // We want to place stations in order of descending weight to keep the busy map sections clean
  var st = Object.keys(graph.nodes).sort(function(a,b){return graph.nodes[b].weight-graph.nodes[a].weight})
  // Try and place nodes if they can be snapped, otherwise nodes can bump each other off if they are closer
  for (var n of st) {
    let node = graph.nodes[n];
    node.x = (node.x) * (1.0/metrics.h_scale) - metrics.x_move;
    node.y = (node.y) * (1.0/metrics.v_scale) - metrics.y_move;

    c = { x: Math.ceil((node.x+metrics.x_avg)/spacing) * spacing,
          y: Math.ceil((node.y+metrics.y_avg)/spacing) * spacing};

    if (!taken[coordinates(c)]){
      taken[coordinates(c)] = node;
      node.placed = true;
      node.x, node.px = c.x, c.x;
      node.y, node.py = c.y, c.y;  
    } else if (taken[coordinates(c)] && dist2d(node, c) < dist2d(taken[coordinates(c)], c)) {
      let old = taken[coordinates(c)];
      old.placed = false;
      taken[coordinates(c)] = node;
      node.placed = true;
      node.x, node.px = c.x, c.x;
      node.y, node.py = c.y, c.y;
    }
  }

  // If we have: (a)  x  (c) [where ac is octilinear, and b has no other links]
  //               \     /
  //                \   /
  //                 (b) 
  // Transform this into: (a)--(b)--(c) [as long as x is not taken]

  for (var line in metro_lines) {
    line = metro_lines[line];
    for (var s=1; s<line.length; s++) {
      let a=graph.nodes[line[s-1][0]];
      let b=graph.nodes[line[s][0]];
      let c=graph.nodes[line[s][1]];
      let candidate = {x:(a.px+c.px)/2.0, y:(a.py+c.py)/2.0};

      if (octilinear(a, c) && b.weight <= 2 && !taken[coordinates(candidate)])  {
        taken[coordinates(b)] = false;
        taken[coordinates(candidate)] = b;
        b.x, b.px = candidate.x, candidate.x;
        b.y, b.py = candidate.y, candidate.y;
        b.placed = true;
      }
    }
  }
  // I'm not even sure why this is needed but like, it really is.
  for (var n=0; n<graph.nodes.length; n++) {
    graph.nodes[n].px = graph.nodes[n].x;
    graph.nodes[n].py = graph.nodes[n].y;
  }

  // If we have: (a)  x  (c) [where ac is octilinear, and b has no other links]
  //               \     /
  //                \   /
  //                 (b) 
  // Transform this into: (a)--(b)--(c) 
  // [EVEN IF x IS TAKEN OR B IS PLACED ALREADY]

  for (var line in metro_lines) {
    line = metro_lines[line];
    for (var s=line.length-1; s>0; s--) {
      let a=graph.nodes[line[s][1]];
      let b=graph.nodes[line[s-1][1]];
      let c=graph.nodes[line[s-1][0]];
      let candidate = {x:(a.px+c.px)/2.0, y:(a.py+c.py)/2.0};

      if (octilinear(a, c) && b.weight == 2)  {
        taken[coordinates(b)] = false;
        taken[coordinates(candidate)] = b;
        b.x = candidate.x; b.px = candidate.x;
        b.y = candidate.y; b.py = candidate.y;
        b.placed = true;
      }
    }
  }

  // If we have: (a)          [where b has not been placed]
  //               \     
  //                \   
  //                 (b)--(c) 
  //
  // Transform this into: (a)
  //                        \     
  //                        (b)
  //                          \
  //                          (c) 
  // [EVEN IF AC NOT OCTILINEAR OR B IS ON OTHER LINES]

  for (var line in metro_lines) {
  line = metro_lines[line];
    for (var s=1; s<line.length; s++) {
      let a=graph.nodes[line[s-1][0]];
      let b=graph.nodes[line[s][0]];
      let c=graph.nodes[line[s][1]];
      let candidate = {x:(a.px+c.px)/2.0, y:(a.py+c.py)/2.0}; 

      if (!b.placed)  {
        taken[coordinates(b)] = false;
        taken[coordinates(candidate)] = b;
        b.x, b.px = candidate.x, candidate.x;
        b.y, b.py = candidate.y, candidate.y;
        a.placed = true;
        b.placed = true;
        c.placed = true;
      }
    }
  }

  var metrics = getMetrics(graph, spacing);

  // We've moved around a lot so the map probably need rescaling & recentering
  for (var n=0; n<graph.nodes.length; n++) {
    let node = graph.nodes[n];
    node.x = (node.px) * (1.0/metrics.h_scale);
    node.y = (node.py) * (1.0/metrics.v_scale);
    node.px = node.x;
    node.py = node.y;
  }

  // Headcount; how many stations couldn't we place?
  taken = {};
  for (var n=0; n<graph.nodes.length; n++) {
    if (taken[coordinates(graph.nodes[n])]) {
      taken[coordinates(graph.nodes[n])] = 1;
    } else {
      taken[coordinates(graph.nodes[n])] = 1;
    }
  }
  force.start();
  console.debug("octilinearity:", octilinearity());
  console.debug("lineStraightness:", lineStraightness());
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

// This will fail if basically any points are drawn on top of each other
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
      total+= theta;
    }
  }
  return total;
}

move(2000);
setTimeout(function(){
  snap(); 
}, 2500);

function timeSince(date) {
    var seconds = Math.floor((new Date() - date) / 1000);
    var interval = Math.floor(seconds / 31536000);

    if (interval > 1) {
        return interval + " years";
    }
    interval = Math.floor(seconds / 2592000);
    if (interval > 1) {
        return interval + " months";
    }
    interval = Math.floor(seconds / 86400);
    if (interval > 1) {
        return interval + " days";
    }
    interval = Math.floor(seconds / 3600);
    if (interval > 1) {
        return interval + " hours";
    }
    interval = Math.floor(seconds / 60);
    if (interval > 1) {
        return interval + " minutes";
    }
    return Math.floor(seconds) + " seconds";
}

function showArticle(data) {
  $('#article-container').get(0).innerHTML = "<h1>"+data.title+"</h1>"+"<h2>"+timeSince(data.date)+" ago</h2>"+ data.html;
    //`<h1>${data.title}</h1><h2>${data.date}</h2><img src='${data.img}'/>`
}

$('#graphPane').click(function() {
  $("#cards").hide();
  $('#feedPane').removeClass("active");
  $("#graph").show();
  $("#article-container").show();
  $("body")[0].style.overflow = "hidden";
  $('#graphPane').addClass("active");
});

$("#feedPane").click(function() {
  $("#graph").hide();
  $("#article-container").hide();
  $('#graphPane').removeClass("active");
  $("#cards").show();
  $("body")[0].style.overflow = "scroll";
  $('#feedPane').addClass("active");
});

 $("#graphPane").trigger("click");
drawGraph(graph);