document.addEventListener("DOMContentLoaded", function () {
    const raw = document.getElementById("plot-data");
    if (!raw) return;

    const plotDataRaw = JSON.parse(raw.textContent);
    const traces = [];
    const layout = {
        title: "時系列プロット",
        xaxis: { title: "時刻" },
        yaxis: {
            titlefont: { color: "blue" },
            tickfont: { color: "blue" },
            showticklabels: true,
            showgrid: true,
            side: "left",
            position: 0.0
        },
        yaxis2: {
            titlefont: { color: "red" },
            tickfont: { color: "red" },
            overlaying: "y",
            side: "right",
            position: 1.0,
            showticklabels: true,
            showgrid: false
        },
        yaxis3: {
            titlefont: { color: "green" },
            tickfont: { color: "green" },
            overlaying: "y",
            side: "left",
            position: 0.5,
            showticklabels: true,
            showgrid: false
        },
        annotations: []
    };

    const axes = ["y", "y2", "y3"];
    const colors = ["blue", "red", "green"];

    for (let i = 0; i < plotDataRaw.length && i < 3; i++) {
        const trace = plotDataRaw[i];
        traces.push({
            x: trace.x,
            y: trace.y,
            name: trace.name,
            mode: "lines+markers",
            yaxis: axes[i],
            line: { color: colors[i] },
            hovertemplate: `%{x}<br>${trace.name}: %{y}<extra></extra>`
        });

        layout.annotations.push({
            xref: "paper",
            yref: "paper",
            x: i === 0 ? 0 : i === 1 ? 1 : 0.5,
            y: 1.1,
            xanchor: "center",
            text: trace.name,
            showarrow: false,
            font: { color: colors[i], size: 14 }
        });
    }

    Plotly.newPlot("plot", traces, layout);
});
