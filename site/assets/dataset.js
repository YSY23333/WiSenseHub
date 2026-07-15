const escapeHtml = value => String(value ?? "").replace(/[&<>'"]/g, char => ({"&":"&amp;","<":"&lt;",">":"&gt;","'":"&#39;",'"':"&quot;"}[char]));
const pretty = value => String(value).replaceAll("_", " ").replaceAll("-", " ").replace(/\b\w/g, letter => letter.toUpperCase());

function factRows(object) {
  return Object.entries(object || {}).map(([key, value]) => `<div><dt>${pretty(key)}</dt><dd>${formatValue(value)}</dd></div>`).join("");
}

function formatValue(value) {
  if (value === null || value === undefined || value === "") return "Not reported";
  if (Array.isArray(value)) return value.map(escapeHtml).join(", ");
  if (typeof value === "object") {
    return Object.entries(value).map(([key, item]) => `<div class="label-line"><span class="label-key">${escapeHtml(pretty(key))}:</span> ${escapeHtml(String(item))}</div>`).join("");
  }
  return escapeHtml(String(value));
}

const formatBytes = bytes => {
  if (!bytes) return "—";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

function renderTree(entries, depth = 0) {
  if (!entries?.length) return `<p class="structure-empty">No hosted sample files yet.</p>`;
  return `<ul class="file-tree">${entries.map(entry => {
    if (entry.type === "dir") {
      const openAttr = depth < 1 ? " open" : "";
      return `<li class="tree-dir"><details${openAttr}><summary><span class="tree-name">${escapeHtml(entry.name)}/</span></summary>${renderTree(entry.children || [], depth + 1)}</details></li>`;
    }
    return `<li class="tree-file"><span class="tree-name">${escapeHtml(entry.name)}</span><small>${formatBytes(entry.bytes)}</small></li>`;
  }).join("")}</ul>`;
}

function collectionSettingSection(dataset) {
  const collection = dataset.collection || {...dataset.settings, ...dataset.hardware};
  const order = [
    ["device", "Device"],
    ["distance", "Distance"],
    ["subjects", "Subjects"],
    ["labels", "Labels"],
    ["scenario_labels", "Scenario / labels"],
    ["band", "Band"],
    ["subcarriers", "Subcarriers"],
    ["subcarrier_spacing", "Subcarrier spacing"],
    ["sampling_rate_hz", "Sampling rate"],
    ["clip_length", "Clip length"],
    ["scenario", "Scenario"],
  ];
  const rows = order
    .filter(([key]) => collection[key] !== undefined && collection[key] !== null && collection[key] !== "")
    .map(([key, label]) => `<tr><th scope="row">${escapeHtml(label)}</th><td>${formatValue(collection[key])}</td></tr>`)
    .join("");
  return `<section class="collection-setting"><h2>Collection setting</h2><div class="table-scroll"><table class="collection-table"><tbody>${rows}</tbody></table></div></section>`;
}

function setupFigureSection(dataset, sample) {
  const figures = sample?.setup_figures || (sample?.setup_figure ? [{ image: sample.setup_figure, source: sample.figure_source }] : []);
  if (!figures.length) return "";
  const cards = figures.map((figure, index) => {
    const source = figure.source;
    const attribution = source ? `<figcaption class="figure-source">Source: <a href="${escapeHtml(source.url)}">${escapeHtml(source.label)}</a></figcaption>` : "";
    const suffix = figures.length > 1 ? ` ${index + 1}` : "";
    return `<figure class="setup-figure"><img src="${escapeHtml(figure.image)}" alt="Experimental setup${suffix} for ${escapeHtml(dataset.name)}" loading="lazy">${attribution}</figure>`;
  }).join("");
  return `<section class="setup-figure-top"><h2>Experimental Setup</h2><div class="setup-figures">${cards}</div></section>`;
}

function sampleRequirement(sample) {
  const req = sample?.sample_requirement;
  if (!req) return "";
  return `<div class="sample-requirement"><h3>Required sample coverage</h3><dl class="facts compact">
    <div><dt>Task</dt><dd>${escapeHtml(req.task)}</dd></div>
    <div><dt>Task label</dt><dd>${escapeHtml(req.task_label)}</dd></div>
    <div><dt>Setting</dt><dd><code>${escapeHtml(req.setting)}</code></dd></div>
    <div><dt>Setting note</dt><dd>${escapeHtml(req.setting_note)}</dd></div>
  </dl></div>`;
}

function sampleStructureSection(sample) {
  return `<details class="sample-structure" open><summary><h3>Sample structure</h3><span class="structure-hint">${sample.file_count || 0} hosted files — click folders to expand</span></summary>${renderTree(sample.file_tree || [])}</details>`;
}

function localGenerationSection(sample) {
  const commands = sample?.local_generation || [];
  if (!commands.length) return "";
  return `<details class="view-options" open><summary>Generate this sample locally</summary><div class="example-command compact"><pre><code>${escapeHtml(commands.join("\n"))}</code></pre></div><p>Use this path when the original release is gated, too large, or cannot be redistributed directly by the hub.</p></details>`;
}

function panel(title, caption, src) {
  return src ? `<figure class="preview-panel compact"><figcaption><strong>${escapeHtml(title)}</strong><span>${escapeHtml(caption || "")}</span></figcaption><img src="${escapeHtml(src)}" alt="${escapeHtml(title)} CSI amplitude heatmap" loading="lazy"></figure>` : "";
}

function sampleSections(dataset, sample) {
  if (!sample) return `<section><h2>Data sample</h2><p class="setting-help">Sample manifest has not been generated yet.</p></section>`;
  const hosted = sample.status === "ok" && sample.sample_zip;
  const download = hosted
    ? `<div class="sample-download"><a class="button primary" href="${escapeHtml(sample.sample_zip)}" download>Download sample (${formatBytes(sample.zip_bytes)})</a><small>${sample.file_count || 0} hosted file(s)</small></div>`
    : `<p class="sample-status planned">Sample package planned. Original data is not redistributed here unless the release terms allow it.</p>`;
  const previews = sample.previews || {};
  const compare = (previews.before || previews.after)
    ? `<section class="preview-section compact"><h2>Before / after standardization</h2><p class="setting-help preview-lead">Paper-style amplitude heatmaps: <strong>x = time</strong>, <strong>y = subcarrier/channel index</strong>.</p><div class="preview-pair compact">${panel("Original", "official release view", previews.before)}${panel("Standardized", "task-profile NPZ view", previews.after)}</div></section>`
    : "";
  const labelPanels = (sample.label_previews || []).map(item => panel(item.label, item.kind || "standardized clip", item.image)).join("");
  const labels = labelPanels
    ? `<section class="preview-section compact"><h2>Standardized visualization by task label</h2><div class="preview-label-grid">${labelPanels}</div></section>`
    : `<section><h2>Standardized visualization by task label</h2><p class="setting-help">No label preview image is hosted yet. Run the local generation command after placing official files under <code>data/${escapeHtml(dataset.id)}/original/</code>.</p></section>`;
  return `<section><h2>Data sample</h2><p>${escapeHtml(sample.note || "Small subset preserving the source layout and standardized output.")}</p>${download}${sampleRequirement(sample)}${sampleStructureSection(sample)}${localGenerationSection(sample)}</section>${compare}${labels}`;
}

function taskProfileSection(dataset) {
  const rows = (dataset.task_profile_defaults || []).map(item => `<tr><td><code>${escapeHtml(item.profile)}</code></td><td>${item.target_rate_hz ? `${item.target_rate_hz} Hz` : "native"}</td><td>${item.duration_s ? `${item.duration_s} s` : "native/continuous"}</td><td>${escapeHtml(item.description)}</td></tr>`).join("");
  if (!rows) return "";
  return `<section><h2>Task-specific standardization</h2><div class="table-scroll"><table class="settings-table"><thead><tr><th>Profile</th><th>Rate</th><th>Interval</th><th>Use case</th></tr></thead><tbody>${rows}</tbody></table></div><p class="setting-help">The native adapter output is preserved. A task-profile view can be produced with <code>--task</code>; for example vital-sign views use 10 Hz while general sensing uses 100 Hz.</p></section>`;
}

async function init() {
  const id = new URLSearchParams(location.search).get("id");
  const catalog = await (await fetch("data/catalog.json")).json();
  const dataset = catalog.datasets.find(item => item.id === id);
  if (!dataset) throw new Error("Dataset entry not found");
  let sample = null;
  try {
    const samples = await (await fetch("data/samples.json")).json();
    sample = samples.datasets?.[id] || null;
  } catch { /* samples.json is optional */ }
  document.title = `${dataset.name} — WiSenseHub`;
  const taskNames = dataset.tasks.map(id => catalog.tasks.find(task => task.id === id)?.name || id);
  const splitConfig = dataset.split_settings;
  const example = dataset.conversion_example;
  const primaryTask = dataset.tasks[0] || "general-sensing";
  const settingRows = splitConfig.settings.map(item => `<tr><td><code>${escapeHtml(item.id)}</code>${item.id === splitConfig.default ? " <small>default</small>" : ""}</td><td>${pretty(item.kind)}</td><td>${pretty(item.provenance)}</td><td>${escapeHtml(item.group_by || "—")}</td></tr>`).join("");
  const prepareSection = `<section><h2>Convert and split</h2><div class="example-command compact"><pre><code>pip install -e ".[data]"
wisensehub settings ${escapeHtml(dataset.id)}
wisensehub prepare ${escapeHtml(dataset.id)} --setting ${escapeHtml(splitConfig.default)} --task ${escapeHtml(primaryTask)} --data-root data</code></pre></div><p>Place the intact official release under <code>data/${escapeHtml(dataset.id)}/original/</code>. The <strong>${escapeHtml(dataset.conversion.handler)}</strong> adapter writes native NPZ tensors, sidecars, quality reports, and a reproducible split manifest.</p><details class="view-options"><summary>Optional fixed-size model view</summary><div class="example-command compact"><pre><code>wisensehub prepare ${escapeHtml(dataset.id)} \\
  --setting ${escapeHtml(splitConfig.default)} \\
  --data-root data \\
  --task ${escapeHtml(primaryTask)} \\
  --target-length 128 \\
  --interpolation linear \\
  --layout link-subcarrier</code></pre></div><p>Native files stay in <code>standardized/</code>. Derived views are written to <code>standardized/views/</code> and record <code>derived_from</code>, task profile, target length/rate, interpolation, and layout.</p></details><dl class="facts"><div><dt>Implementation</dt><dd>${pretty(dataset.conversion.implementation)}</dd></div><div><dt>Recognized layout</dt><dd><code>${dataset.conversion.patterns.map(escapeHtml).join("<br>")}</code></dd></div><div><dt>Adapter evidence</dt><dd><a href="${escapeHtml(dataset.conversion.official_reference)}">Official loader or schema</a></dd></div></dl><div class="table-scroll"><table class="settings-table"><thead><tr><th>Setting</th><th>Method</th><th>Provenance</th><th>Group</th></tr></thead><tbody>${settingRows}</tbody></table></div><p class="setting-help">For cross-group protocols, use <code>--holdout</code> with an official group ID. If filenames do not encode the group, add <code>original/metadata.csv</code>.</p></section>`;
  const inspectCommand = `python - <<'PY'\nfrom pathlib import Path\nimport numpy as np\np = next(Path("data/${dataset.id}/standardized").glob("**/*.npz"))\nx = np.load(p)\nprint(p)\nfor name in x.files:\n    print(name, x[name].shape, x[name].dtype)\nPY`;
  const conversionExampleSection = `<section class="conversion-example"><p class="eyebrow">DATASET-SPECIFIC WALKTHROUGH</p><h2>Conversion example</h2><ol class="example-steps"><li><strong>Place one official source</strong><pre><code>data/${escapeHtml(dataset.id)}/original/${escapeHtml(example.source_path)}</code></pre></li><li><strong>Run the adapter and default split</strong><pre><code>wisensehub prepare ${escapeHtml(dataset.id)} \\
  --data-root data \\
  --setting ${escapeHtml(splitConfig.default)} \\
  --task ${escapeHtml(primaryTask)} \\
  --limit 1</code></pre></li><li><strong>Inspect the generated tensor</strong><pre><code>${escapeHtml(inspectCommand)}</code></pre></li></ol><dl class="facts example-output"><div><dt>Primary array</dt><dd><code>${escapeHtml(example.primary_array)}</code></dd></div><div><dt>Expected shape</dt><dd><code>${escapeHtml(example.expected_shape)}</code></dd></div></dl><p class="setting-help">${escapeHtml(example.note)}</p></section>`;
  const outputPreviewSection = `<section><h2>Standardized output preview</h2><dl class="facts example-output"><div><dt>Native NPZ</dt><dd><code>data/${escapeHtml(dataset.id)}/standardized/*.npz</code></dd></div><div><dt>Derived view</dt><dd><code>data/${escapeHtml(dataset.id)}/standardized/views/*.npz</code></dd></div><div><dt>Primary array</dt><dd><code>${escapeHtml(example.primary_array)}</code></dd></div><div><dt>Typical shape</dt><dd><code>${escapeHtml(example.expected_shape)}</code></dd></div></dl><p class="setting-help">Canonical CSI uses <code>[T,L,S]</code> or <code>[N,T,L,S]</code>. <code>--layout link-subcarrier</code> exports <code>[T,F]</code> or <code>[N,T,F]</code> for model-ready features.</p></section>`;
  document.querySelector("#dataset-detail").innerHTML = `
    <a class="back-link" href="index.html#datasets">← All datasets</a>
    <section class="detail-hero"><p class="eyebrow">DATASET · ${dataset.year}</p><h1>${escapeHtml(dataset.name)}</h1><p>${escapeHtml(dataset.summary)}</p><div class="task-tags large">${taskNames.map(name => `<span>${escapeHtml(name)}</span>`).join("")}</div></section>
    ${setupFigureSection(dataset, sample)}
    <div class="detail-grid">
      <div class="detail-main">
        ${collectionSettingSection(dataset)}
        <section><h2>Scale</h2><dl class="facts">${factRows(dataset.scale)}</dl></section>
        <section><h2>Standardization plan</h2><div class="standard-note"><strong>${pretty(dataset.standardization.status)}</strong><code>${escapeHtml(dataset.standardization.profile)}</code><p>${escapeHtml(dataset.standardization.notes)}</p></div></section>
        ${taskProfileSection(dataset)}
        ${sampleSections(dataset, sample)}
        ${prepareSection}${conversionExampleSection}${outputPreviewSection}
        <section><h2>Evidence</h2><ul class="source-list">${dataset.sources.map(source => `<li><span>${pretty(source.type)}</span><a href="${escapeHtml(source.url)}">${escapeHtml(source.url)}</a></li>`).join("")}</ul></section>
      </div>
      <aside class="access-panel"><h2>Original release</h2><dl><div><dt>Access</dt><dd>${pretty(dataset.original.access)}</dd></div><div><dt>License</dt><dd>${escapeHtml(dataset.original.license)}</dd></div><div><dt>Redistribution</dt><dd>${pretty(dataset.original.redistribution)}</dd></div><div><dt>Formats</dt><dd>${escapeHtml(dataset.original.formats.join(", ") || "Not confirmed")}</dd></div></dl><a class="button primary full" href="${escapeHtml(dataset.original.download_page || dataset.original.landing_page)}">Open original source</a><p class="verification">Metadata verified ${dataset.verified_at}</p></aside>
    </div>`;
}

init().catch(error => { document.querySelector("#dataset-detail").innerHTML = `<a class="back-link" href="index.html">← Home</a><h1>Dataset unavailable</h1><p>${escapeHtml(error.message)}</p>`; });
