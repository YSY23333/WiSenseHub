const escapeHtml = value => String(value ?? "").replace(/[&<>'"]/g, char => ({"&":"&amp;","<":"&lt;",">":"&gt;","'":"&#39;",'"':"&quot;"}[char]));
const pretty = value => String(value).replaceAll("_", " ").replace(/\b\w/g, letter => letter.toUpperCase());

function factRows(object) {
  return Object.entries(object).map(([key, value]) => `<div><dt>${pretty(key)}</dt><dd>${escapeHtml(value === null ? "Not reported" : value)}</dd></div>`).join("");
}

async function init() {
  const id = new URLSearchParams(location.search).get("id");
  const catalog = await (await fetch("data/catalog.json")).json();
  const dataset = catalog.datasets.find(item => item.id === id);
  if (!dataset) throw new Error("Dataset entry not found");
  document.title = `${dataset.name} — WiSenseHub`;
  const taskNames = dataset.tasks.map(id => catalog.tasks.find(task => task.id === id)?.name || id);
  const splitConfig = dataset.split_settings;
  const example = dataset.conversion_example;
  const settingRows = splitConfig.settings.map(item => `<tr><td><code>${escapeHtml(item.id)}</code>${item.id === splitConfig.default ? " <small>default</small>" : ""}</td><td>${pretty(item.kind)}</td><td>${pretty(item.provenance)}</td><td>${escapeHtml(item.group_by || "—")}</td></tr>`).join("");
  const prepareSection = `<section><h2>Convert and split</h2><div class="example-command compact"><pre><code>pip install -e \".[data]\"\nwisensehub settings ${escapeHtml(dataset.id)}\nwisensehub prepare ${escapeHtml(dataset.id)} --setting ${escapeHtml(splitConfig.default)} --data-root data</code></pre></div><p>Place the intact official release under <code>data/${escapeHtml(dataset.id)}/original/</code>. The <strong>${escapeHtml(dataset.conversion.handler)}</strong> adapter writes NPZ tensors, sidecars, quality reports, and a reproducible split manifest.</p><dl class="facts"><div><dt>Implementation</dt><dd>${pretty(dataset.conversion.implementation)}</dd></div><div><dt>Recognized layout</dt><dd><code>${dataset.conversion.patterns.map(escapeHtml).join("<br>")}</code></dd></div><div><dt>Adapter evidence</dt><dd><a href="${escapeHtml(dataset.conversion.official_reference)}">Official loader or schema</a></dd></div></dl><div class="table-scroll"><table class="settings-table"><thead><tr><th>Setting</th><th>Method</th><th>Provenance</th><th>Group</th></tr></thead><tbody>${settingRows}</tbody></table></div><p class="setting-help">For cross-group protocols, use <code>--holdout 3</code> (or another official group ID). If filenames do not encode the group, add <code>original/metadata.csv</code>.</p></section>`;
  const inspectCommand = `python - <<'PY'\nfrom pathlib import Path\nimport numpy as np\np = next(Path(\"data/${dataset.id}/standardized\").glob(\"*.npz\"))\nx = np.load(p)\nprint(p)\nfor name in x.files:\n    print(name, x[name].shape, x[name].dtype)\nPY`;
  const conversionExampleSection = `<section class="conversion-example"><p class="eyebrow">DATASET-SPECIFIC WALKTHROUGH</p><h2>Conversion example</h2><ol class="example-steps"><li><strong>Place one official source</strong><pre><code>data/${escapeHtml(dataset.id)}/original/${escapeHtml(example.source_path)}</code></pre></li><li><strong>Run the adapter and default split</strong><pre><code>wisensehub prepare ${escapeHtml(dataset.id)} \\\n  --data-root data \\\n  --setting ${escapeHtml(splitConfig.default)} \\\n  --limit 1</code></pre></li><li><strong>Inspect the generated tensor</strong><pre><code>${escapeHtml(inspectCommand)}</code></pre></li></ol><dl class="facts example-output"><div><dt>Primary array</dt><dd><code>${escapeHtml(example.primary_array)}</code></dd></div><div><dt>Expected shape</dt><dd><code>${escapeHtml(example.expected_shape)}</code></dd></div></dl><p class="setting-help">${escapeHtml(example.note)}</p></section>`;
  document.querySelector("#dataset-detail").innerHTML = `
    <a class="back-link" href="index.html#datasets">← All datasets</a>
    <section class="detail-hero"><p class="eyebrow">DATASET · ${dataset.year}</p><h1>${escapeHtml(dataset.name)}</h1><p>${escapeHtml(dataset.summary)}</p><div class="task-tags large">${taskNames.map(name => `<span>${escapeHtml(name)}</span>`).join("")}</div></section>
    <div class="detail-grid">
      <div class="detail-main">
        <section><h2>Collection setting</h2><dl class="facts">${factRows({...dataset.settings, ...dataset.hardware})}</dl></section>
        <section><h2>Scale</h2><dl class="facts">${factRows(dataset.scale)}</dl></section>
        <section><h2>Standardization plan</h2><div class="standard-note"><strong>${pretty(dataset.standardization.status)}</strong><code>${escapeHtml(dataset.standardization.profile)}</code><p>${escapeHtml(dataset.standardization.notes)}</p></div></section>${prepareSection}${conversionExampleSection}
        <section><h2>Evidence</h2><ul class="source-list">${dataset.sources.map(source => `<li><span>${pretty(source.type)}</span><a href="${escapeHtml(source.url)}">${escapeHtml(source.url)}</a></li>`).join("")}</ul></section>
      </div>
      <aside class="access-panel"><h2>Original release</h2><dl><div><dt>Access</dt><dd>${pretty(dataset.original.access)}</dd></div><div><dt>License</dt><dd>${escapeHtml(dataset.original.license)}</dd></div><div><dt>Redistribution</dt><dd>${pretty(dataset.original.redistribution)}</dd></div><div><dt>Formats</dt><dd>${escapeHtml(dataset.original.formats.join(", ") || "Not confirmed")}</dd></div></dl><a class="button primary full" href="${escapeHtml(dataset.original.download_page || dataset.original.landing_page)}">Open original source</a><p class="verification">Metadata verified ${dataset.verified_at}</p></aside>
    </div>`;
}

init().catch(error => { document.querySelector("#dataset-detail").innerHTML = `<a class="back-link" href="index.html">← Home</a><h1>Dataset unavailable</h1><p>${escapeHtml(error.message)}</p>`; });
