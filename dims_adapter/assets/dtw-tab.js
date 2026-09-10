/* DTW gait space — GAIT-attempt.
 *
 * DIMS's analyses ask how much two signals are coupled. This one asks how one
 * must be warped in time to match the other, and plots the cohort in the space
 * those distances define.
 *
 * A pair of streams need not be a pair of people. Here the pairs are the same
 * person under two conditions — walking, and walking while counting backwards
 * in sevens — so the line between a participant's two points is the effect of
 * a cognitive load on their gait.
 *
 * Self-registering per contracts/tab.md; reads only `app.loadJSON`.
 */
(function () {
    'use strict';

    const ASSET = 'assets/dtw/gaitspace.json';

    function theme() { return window.DIMS.theme(); }

    const PATIENT = '#d95926';
    const CONTROL = '#3987e5';

    function colourFor(meta) {
        return meta.group === 'Control' ? CONTROL : PATIENT;
    }

    function gaitSpace(data, container) {
        const traces = [];
        const seen = {};

        data.ids.forEach((id, i) => {
            const m = data.meta[id];
            (seen[m.base] = seen[m.base] || []).push({ id, i, m });
        });

        // One line per participant, from usual walking to dual task. The line
        // is the finding: its length is how far the load moved their gait.
        Object.keys(seen).forEach((base) => {
            const pair = seen[base];
            if (pair.length !== 2) return;
            pair.sort((a, b) => (a.m.walk === '01' ? -1 : 1));
            traces.push({
                x: pair.map((p) => data.coords[p.i][0]),
                y: pair.map((p) => data.coords[p.i][1]),
                mode: 'lines',
                line: { color: colourFor(pair[0].m), width: 2 },
                opacity: 0.55,
                hoverinfo: 'skip',
                showlegend: false,
            });
        });

        for (const [label, group, symbol] of [
            ['Usual walking', '01', 'circle'],
            ['Dual task (serial 7s)', '10', 'diamond'],
        ]) {
            const picked = data.ids
                .map((id, i) => ({ id, i, m: data.meta[id] }))
                .filter((p) => p.m.walk === group);
            traces.push({
                x: picked.map((p) => data.coords[p.i][0]),
                y: picked.map((p) => data.coords[p.i][1]),
                text: picked.map((p) => `${p.id}<br>${p.m.group}, ${p.m.condition}` +
                    `<br>stride CV ${p.m.stride_cv == null ? '—' : p.m.stride_cv.toFixed(1) + '%'}`),
                hovertemplate: '%{text}<extra></extra>',
                mode: 'markers',
                name: label,
                marker: {
                    size: group === '10' ? 13 : 11,
                    symbol,
                    color: picked.map((p) => colourFor(p.m)),
                    line: { color: theme().paper, width: 1.5 },
                },
            });
        }

        Plotly.newPlot(container, traces, {
            title: {
                text: `DTW gait space — ${(100 * data.explained).toFixed(0)}% of distances in 2-D`,
                font: { color: theme().font },
            },
            paper_bgcolor: theme().paper,
            plot_bgcolor: theme().plot,
            font: { color: theme().font },
            xaxis: { title: 'MDS 1', color: theme().font, gridcolor: theme().grid, zeroline: false },
            yaxis: { title: 'MDS 2', color: theme().font, gridcolor: theme().grid,
                     zeroline: false, scaleanchor: 'x', scaleratio: 1 },
            legend: { orientation: 'h', y: -0.18, font: { color: theme().font } },
            margin: { t: 50, r: 20, b: 70, l: 60 },
        }, { displaylogo: false, responsive: true });
    }

    function nullComparison(data, container) {
        const within = data.within_subject;
        const between = data.between_subject;
        Plotly.newPlot(container, [
            {
                x: within.values, type: 'box', name: `same person (n=${within.n})`,
                marker: { color: CONTROL }, boxpoints: 'all', jitter: 0.5, orientation: 'h',
            },
        ], {
            title: {
                text: data.permutation_p == null
                    ? 'A person against themselves, against the null'
                    : `A person against themselves, against the null — p = ${data.permutation_p.toFixed(3)}`,
                font: { color: theme().font },
            },
            shapes: [{
                type: 'line', x0: between.mean, x1: between.mean, y0: -0.5, y1: 0.5,
                line: { color: PATIENT, width: 2, dash: 'dash' },
            }],
            annotations: [{
                x: between.mean, y: 0.42, xanchor: 'left', showarrow: false,
                text: `  mean of ${between.n} pairs of people who never met`,
                font: { color: PATIENT, size: 11 },
            }],
            paper_bgcolor: theme().paper,
            plot_bgcolor: theme().plot,
            font: { color: theme().font },
            xaxis: { title: 'DTW distance (lower = more alike)', color: theme().font, gridcolor: theme().grid },
            yaxis: { showticklabels: false, color: theme().font, gridcolor: theme().grid },
            showlegend: false,
            margin: { t: 50, r: 20, b: 55, l: 30 },
        }, { displaylogo: false, responsive: true });
    }

    window.DIMS.registerTab({
        id: 'gaitspace',
        label: 'DTW gait space',
        order: 60,

        gate(config) { return config && config.include_dtw === true; },

        async onActivate(app, container) {
            const data = await app.loadJSON(ASSET).catch(() => null);
            if (!data) {
                container.innerHTML = '<p style="padding:1em;">No DTW payload. ' +
                    'Build one with <code>python -m dims_adapter.gaitspace &lt;case&gt;</code>.</p>';
                return;
            }
            const problem = window.DIMS.payloadProblem(data, 'DTW output');
            if (problem) { container.innerHTML = `<p style="padding:1em;">${problem}</p>`; return; }

            container.innerHTML = `
              <div id="gaitspacePlot" style="height:520px;"></div>
              <div id="gaitspaceNull" style="height:260px;margin-top:8px;"></div>
              <p style="padding:0 1em 1em;font-size:12px;line-height:1.5;opacity:.75;">
                Each participant appears twice — walking, and walking while counting
                backwards in sevens. <strong>The line between their two points is the
                effect of the cognitive load on their gait.</strong>
                Distances are band-constrained DTW on left-foot ground reaction force,
                z-normalised (so this compares gait <em>shape</em>, not body weight),
                at ${data.sample_rate_hz} Hz with a ${(100 * data.band_fraction).toFixed(0)}% Sakoe-Chiba band.
                <br><br>
                <strong>Read the null before the pattern.</strong> These participants
                never walked together — separate sessions, separate labs — so a
                distance between two of them measures nothing about coordination.
                It is the chance level. Only the same-person distances carry signal.
                <br><br>
                <strong>What this run found.</strong> A person's two walks are closer
                to each other (mean ${data.within_subject.mean == null ? '—' : data.within_subject.mean.toFixed(3)},
                n=${data.within_subject.n}) than two different people are
                (${data.between_subject.mean == null ? '—' : data.between_subject.mean.toFixed(3)},
                n=${data.between_subject.n})${data.permutation_p == null ? '' :
                  `, but with six pairs that is <em>suggestive, not significant</em>:
                   p = ${data.permutation_p.toFixed(3)} over ${data.permutations.toLocaleString()}
                   permutations`}. One participant is a clear outlier and drives much
                of the spread — worth looking at before reading anything into the mean.
              </p>`;
            this._data = data;
            gaitSpace(data, document.getElementById('gaitspacePlot'));
            nullComparison(data, document.getElementById('gaitspaceNull'));
        },

        onUpdate(app) {
            if (!this._data) return;
            gaitSpace(this._data, document.getElementById('gaitspacePlot'));
            nullComparison(this._data, document.getElementById('gaitspaceNull'));
        },
    });
})();
