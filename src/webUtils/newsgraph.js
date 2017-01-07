  var width = window.innerWidth, 
      height = window.innerHeight-document.getElementsByTagName("nav")[0].clientHeight;

  var color = color = d3.scale.ordinal()
              .domain(50)
              .range(["#1596ff", "#ff6401", "#fd85b0", "#fef302", "#03aa4a", "#38d8ce", "#e0d8ff", "#d485ff", "#21fed9", "#a78f7b", "#fe906e", "#fe45c1", "#7c9f10", "#6ea87a", "#0afe7a", "#a6f9fd", "#af83c1", "#ffa103", "#ff576d", "#66c1fe", "#97f1a0", "#3fc104", "#febbc0", "#8494ad", "#a1fe04", "#e0bb10", "#ccd0c7", "#da6bc0", "#b4d404", "#dc7a28", "#09fba9", "#08bf8a", "#ffbcfa"]);

  var radius = d3.scale.sqrt().range([0, 6]);

  var svg = d3.select("body")
      .append("svg")
      .attr("id", "graph")
      .attr("width", width)
      .attr("height", height);

  var force = d3.layout.force()
      .size([width, height])
      .charge(
        function(d){
          return -200*(d.weight>2?4:3); 
      })
      .linkDistance(function(d){
          return 15*(1+Math.max(d.source.lines.length, d.target.lines.length)); 
      })
      .linkStrength(0.7)
      .friction(0.91)
      .alpha(1);

  var metro_lines = NG-METRO-LINES;
  var graph = {
      "nodes": NG-NODES ,
      "links": NG-LINKS
  };

  for (var n=0; n<graph.nodes.length;++n) {
    graph.nodes[n].data.date = new Date(graph.nodes[n].data.date);
  }

  var focusedLine = null;

  function isInterchange(d) {
    return d.lines.length > 1;
  }

  var drawGraph = function (graph) {
      force.nodes(graph.nodes)
          .links(graph.links)
          .on("tick", function() {
            for (var i = 0; i < 10; i++) {
              tick();
            }
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
          .call(force.drag);

      node.on("click", function(d) {
        let lines = d.lines.join('.').replace(' ','-');
        var searchDomain = $('.card.'+lines);
        console.log('.card.'+lines);
        for (var a=0; a<searchDomain.length; ++a) {
          console.log(searchDomain[a].name);
        }
      });

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
              .attr("line", function(d) { return d; })
              .style("fill", color)
              .on("click", function(d){
                var line = d;
                node = svg.selectAll(".node")
                  .data(graph.nodes)
                  .style("visibility", function(d) {
                    if (line===focusedLine) {
                      return "visible";
                    } else {
                      return d.lines.indexOf(line) != -1 ? "visible":"visible";
                    }
                  });
                link = svg.selectAll(".link")
                  .data(graph.links)
                  .style("visibility", function(d) {
                    if (line===focusedLine) {
                      return "visible";
                    } else {
                      return d.line === line ? "visible": "visible";
                    }
                  });
              });

          key.append("text")
              .attr("x", 75)
              .attr("y", 10)
              .attr("dy", 20)
              .text(function(d) { return d; });
      }
  };

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

function snap(){
  var spacing = height/8;
  var metrics = { x_min: width, x_max: 0,
                  y_min: height, y_max: 0,
                  x_avg: 0, y_avg: 0 };

  force.stop();
  for (var n=0; n<graph.nodes.length; n++) {
    let node = graph.nodes[n];
    c = { x: Math.ceil(node.x/spacing) * spacing,
          y: Math.ceil(node.y/spacing) * spacing};

    if (c.x < metrics.x_min) {
      metrics.x_min = c.x;
    }
    if (c.x > metrics.x_max) {
      metrics.x_max = c.x
    }
    if (c.y < metrics.y_min) {
      metrics.y_min = c.y;
    }
    if (c.y > metrics.y_max) {
      metrics.y_max = c.y;
    }
    metrics.x_avg += c.x;
    metrics.y_avg += c.y;
  
    node.x, node.px = c.x, c.x;
    node.y, node.py = c.y, c.y;
  }

  metrics.x_avg /= graph.nodes.length;
  metrics.y_avg /= graph.nodes.length;

  let v_scale = Math.abs(metrics.y_max - metrics.y_min)/(height-2*spacing);
  let h_scale = Math.abs(metrics.x_max - metrics.x_min)/(height-2*spacing); // Deliberate

  var taken = {}
  for (var n=0; n<graph.nodes.length; n++) {
    let node = graph.nodes[n];
    node.x = (node.x-metrics.x_avg) * (1.0/h_scale);
    node.y = (node.y-metrics.y_avg) * (1.0/v_scale);

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

  // for (var line in metro_lines) {
  //   line = metro_lines[line];
  //   for (var s=1; s<line.length; s++) {
  //     let a=graph.nodes[line[s-1][0]];
  //     let b=graph.nodes[line[s][0]];
  //     let c=graph.nodes[line[s][1]];

  //     if (a.weight==1 && octilinear(b, c)) {
  //       let candidate = {x:b.px-(c.px-b.px), y:b.py-(c.py-b.py)};
  //         a.x, a.px = candidate.x, candidate.x;
  //         a.y, a.py = candidate.y, candidate.y;
  //         a.placed = true;
  //     }
  //     if (c.weight==1 && octilinear(a, b)) {
  //       let candidate = {x:b.px+(b.px-a.px), y:b.py+(b.py-a.py)};
  //         c.x, a.px = candidate.x, candidate.x;
  //         c.y, a.py = candidate.y, candidate.y;
  //         c.placed = true;
  //     }
  //   }
  // }
  var unplaced = 0;
  for (var n=0; n<graph.nodes.length; n++) {
    unplaced += graph.nodes[n].placed? 0:1;
  }
  // for (var n=0; n<graph.nodes.length; n++) {
  //   graph.nodes[n].x = 0.8* graph.nodes[n].x;
  //   graph.nodes[n].y = 0.8* graph.nodes[n].y;
  //   // graph.nodes[n].px = graph.nodes[n].x;
  //   // graph.nodes[n].py = graph.nodes[n].y;
  // }
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

var octilinearity = function(){
  var total = 0;
  for (var n=0; n<graph.links.length; n++) {
      let s = graph.links[n].source;
      let t = graph.links[n].target;
      let theta = 4*Math.atan(Math.abs(s.y-t.y)/Math.abs(s.x-t.x));
      total += Math.abs(Math.sin(theta));
    }
  return total;
}

var lineStraightness = function(){
  var total = 0;
  for (var line in metro_lines) {
    line = metro_lines[line];
    for (var s=0; s<line.length-1; s++) {
      let a=graph.nodes[line[s][0]];
      let b=graph.nodes[line[s+1][0]];
      let c=graph.nodes[line[s+1][1]];
      let v1 = {x:a.x - b.x, y:a.y - b.y};
      let v2 = {x:c.x - b.x, y:c.y - b.y};
      v1mag = Math.sqrt(v1.x * v1.x + v1.y * v1.y);
      v1norm = {x:v1.x / v1mag, y:v1.y / v1mag};
      v2mag =  Math.sqrt(v2.x * v2.x + v2.y * v2.y);
      v2norm = {x:v2.x / v2mag, y:v2.y / v2mag};
      res = v1norm.x * v2norm.x + v1norm.y * v2norm.y;
      var theta = Math.acos(res);
      if (theta > Math.PI/2) {
        theta = Math.PI-theta;
      }
      total+= theta;
    }
  }
  return total;
}

force.on('tick', function(e) {
  graph.nodes.forEach(function(d) {
    d.y += (height/2 - d.y) * 1000;
    d.py += (height/2 - d.py) * 1000;
  });
})

function go() {
    move(5*lineStraightness() + 2*octilinearity());
    snap();
}

move(3500);
setTimeout(function(){ snap(); }, 4000);




  $('#graphPane').click(function() {
    $("#cards").attr("hidden", true);
    $('#feedPane').removeClass("active");
    $("#graph").attr("display", "inline");
    $('#graphPane').addClass("active");
  });

  $("#feedPane").click(function() {
    $("#graph").attr("display", "none");
    $('#graphPane').removeClass("active");
    $("#cards").attr("hidden", false);
    $('#feedPane').addClass("active");
  });

   $("#graphPane").trigger("click");
  drawGraph(graph);