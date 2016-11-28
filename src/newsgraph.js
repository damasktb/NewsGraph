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
      .charge(-500)
      .linkDistance(50);

  var graph = {
      "nodes": NG-NODES ,
      "links": NG-LINKS
  };

  var focusedLine = null;

  var drawGraph = function (graph) {
      force.nodes(graph.nodes)
          .links(graph.links)
          .on("tick", tick)
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

      function isInterchange(d) {
        return d.lines.length > 1;
      }

      function fixline(line) {
        let total = graph.links.filter(function(d){return d.line===line}).length;
        let spacing = (width-100)/total;
        var x_i = 50;
        for (var n=0; n<graph.nodes.length;++n) {
          if (graph.nodes[n].lines.indexOf(line) != -1) {
            graph.nodes[n].fixed = true;
            graph.nodes[n].y = height/2;
            graph.nodes[n].py = height/2;
            graph.nodes[n].x = x_i;
            graph.nodes[n].px = x_i;
            x_i += spacing;
          }
        }
        tick();
      }

      function unfixline(line) {
        force.nodes().forEach(function(d) { d.fixed = false; });
        force.start();
      }


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
                if (line===focusedLine) {
                  unfixline(focusedLine);
                  focusedLine = null;
                } else {
                  focusedLine = line;
                  fixline(focusedLine);
                }
              });

          key.append("text")
              .attr("x", 75)
              .attr("y", 10)
              .attr("dy", 20)
              .text(function(d) { return d; });
      }
  };

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