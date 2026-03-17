data = {
    type: 'scatterpolar',
    line: {
        color: "#00cc7a",
    },
    // mode: 'lines',
}
layout = {
    polar: {
        gridshape: "linear",
        radialaxis: {
            visible: true,
            range: [0, 100],
            gridcolor: "#FFFFFF",
            linecolor: '#FFFFFF',
            ticks: "",
            showticklabels: false,
        },
        angularaxis: {
            gridcolor: '#FFFFFF',
            linecolor: '#FFFFFF',
            tickfont: {
                size: 14,
            },
        },
        bgcolor: '#E5ECF6',
        line: "white",
    },
    showlegend: false,
    hovermode: false,
    // paper_bgcolor: 'black',
    plot_bgcolor: 'lightblue',
    linecolor: "#FFFFFF",
}
config = {
    "responsive": false,
    "displayModeBar": false,
    'scrollZoom': false,
    "staticPlot": true
}

document.addEventListener("DOMContentLoaded", function () {
    chart = document.querySelector("#chart");
    value = JSON.parse(chart.dataset.chart);
    // Plotly.newPlot(charts[x].id, data, layout);

    _data = data;
    _data["theta"] = value["theta"];
    _data["r"] = value["r"];

    _data["theta"].push(value["theta"][0]);
    _data["r"].push(value["r"][0]);

    Plotly.newPlot( chart, [_data], layout, config);

    tspan = document.querySelectorAll("tspan");

    for (var y = 0; y < tspan.length; y++) {
        if (value["class"][tspan[y].innerHTML] != undefined) {
            value["class"][tspan[y].innerHTML].forEach(element => {
                tspan[y].classList.add(element)
            });
        }
    }
});
