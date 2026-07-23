# Task: Airport departures board widget

Build `index.html` in this directory: a polished, dark-themed airport
departures board rendering the data from `data.js` (load it via
`<script src="data.js"></script>`; do not modify data.js). Vanilla
HTML/CSS/JS only - no CDNs, no frameworks, works offline from file://.

## Required DOM contract (graded by automated browser checks)
- `<table id="board">` with a `<thead>` and `<tbody>`.
- Header cells: `<th data-key="flight|city|time|gate|status">` (5 columns:
  Flight, City, Time, Gate, Status).
- Each data row: `<tr data-flight="CS101">` (the flight code) inside tbody.
- Status cell contains `<span class="chip" data-status="On Time|Boarding|Delayed|Cancelled">`
  showing the status text, color-coded: On Time = green, Boarding = blue,
  Delayed = amber/orange, Cancelled = red (distinct colors required).
- `<input id="filter">`: typing filters rows to those whose flight code OR
  city contains the text (case-insensitive). Filtering re-renders rows and
  updates the count.
- `<span id="count">` always shows exactly: `N flights` (e.g. `12 flights`,
  `1 flights` is NOT required - use `1 flight` for singular).
- Clicking a `<th>` sorts rows by that column; clicking the same header again
  reverses the order. The active header must carry `aria-sort="ascending"` or
  `"descending"`; other headers must have no aria-sort. Time sorts
  chronologically; flight/city/gate/status sort as strings.
- Initial state: sorted by time ascending, all 12 rows, count shows
  `12 flights`.

## Aesthetics (also scored, secondary)
Make it look like a real airport departure board: dark background, clear
typographic hierarchy, monospace-styled flight/time columns, hover states,
polished chips. No horizontal scroll at 1200px wide.

Work in this directory only.
