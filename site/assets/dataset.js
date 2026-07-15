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

function structureBlock({ kind, badge, title, hint, tree, empty }) {
  return `<article class="structure-block structure-block-${escapeHtml(kind)}"><header><span class="structure-badge">${escapeHtml(badge)}</span><h4>${escapeHtml(title)}</h4><p class="structure-pane-hint">${escapeHtml(hint)}</p></header><div class="structure-block-body">${tree.length ? renderTree(tree) : `<p class="structure-empty">${escapeHtml(empty)}</p>`}</div></article>`;
}

function sampleStructureSection(sample) {
  const originalTree = sample.original_file_tree || [];
  const standardizedTree = sample.standardized_file_tree || [];
  const usecaseTree = sample.usecase_file_tree || [];
  if (!(originalTree.length || standardizedTree.length || usecaseTree.length)) {
    return `<details class="sample-structure" open><summary><h3>Sample structure</h3><span class="structure-hint">${sample.file_count || 0} files — click folders to expand</span></summary>${renderTree(sample.file_tree || [])}</details>`;
  }
  const original = structureBlock({ kind: "original", badge: "1 · Original", title: "Original dataset", hint: `Official release layout · ${sample.original_file_count || 0} files`, tree: originalTree, empty: "No original sample files hosted." });
  const standardized = structureBlock({ kind: "standardized", badge: "2 · Standardized", title: "Standardized structure", hint: `Prepare output under data/…/standardized/ · ${sample.standardized_file_count || 0} files`, tree: standardizedTree, empty: "Run wisensehub prepare to create standardized NPZ + JSON." });
  const usecase = structureBlock({ kind: "usecase", badge: "3 · Use case", title: "by_label packaging", hint: `One derived example: one folder per label · ${sample.usecase_file_count || 0} files`, tree: usecaseTree.length ? [{ name: "by_label", type: "dir", children: usecaseTree }] : [], empty: "No by_label use-case samples yet." });
  return `<details class="sample-structure" open><summary><h3>Sample structure</h3><span class="structure-hint">original → standardized → one use case</span></summary><div class="structure-split structure-split-3">${original}<div class="structure-vs" aria-hidden="true">→</div>${standardized}<div class="structure-vs" aria-hidden="true">→</div>${usecase}</div></details>`;
}

function dimTable(dimensions) {
  if (!dimensions?.length) return "";
  const rows = dimensions.map(item => `<tr><td><code>${escapeHtml(item.axis)}</code></td><td><code>${escapeHtml(item.size)}</code></td><td>${escapeHtml(item.meaning)}</td></tr>`).join("");
  return `<div class="preview-dim-block"><h4>Tensor dimensions</h4><table class="compact-table"><thead><tr><th>Axis</th><th>Size</th><th>Meaning</th></tr></thead><tbody>${rows}</tbody></table></div>`;
}

function metaCard(title, block) {
  if (!block) return "";
  return `<article class="preview-meta-card"><h3>${escapeHtml(title)}</h3><dl class="facts compact">${factRows(block.profile)}</dl>${dimTable(block.dimensions)}</article>`;
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
  const licenseNote = dataset.original?.redistribution === "allowed" ? "The original license permits redistribution." : "Check the original license before reusing this sample beyond local evaluation.";
  const packageParts = [sample.original_file_count ? "original" : null, sample.standardized_file_count ? "standardized" : null, sample.usecase_file_count ? "by_label use case" : null].filter(Boolean).join(" · ");
  const download = hosted
    ? `<div class="sample-download"><a class="button primary" href="${escapeHtml(sample.sample_zip)}" download>Download sample (${formatBytes(sample.zip_bytes)})</a><small>${sample.file_count || 0} files · ${formatBytes(sample.sample_bytes)} uncompressed${packageParts ? ` · includes ${packageParts}` : ""} · ${escapeHtml(licenseNote)}</small></div>`
    : `<p class="sample-status planned">Sample package planned. Original data is not redistributed here unless the release terms allow it.</p>`;
  const previews = sample.previews || {};
  const grid = sample.standardized_view?.profile || {};
  const gridNote = grid.tensor_shape ? `Standardized view: <strong>${escapeHtml(grid.tensor_shape)}</strong>${grid.sampling_rate ? ` at <strong>${escapeHtml(grid.sampling_rate)}</strong>` : ""}.` : "";
  const compare = (previews.before || previews.after)
    ? `<section class="preview-section compact"><h2>CSI preview</h2><p class="setting-help preview-lead">Paper-style amplitude heatmaps: <strong>x = time</strong>, <strong>y = subcarrier</strong>. ${gridNote}</p><div class="preview-compare-meta">${metaCard("Original release", sample.original)}${metaCard("Standardized view", sample.standardized_view)}</div><div class="preview-pair compact">${panel("Original", sample.preview_source_file || "source file", previews.before)}${panel("Standardized", "task-profile view", previews.after)}</div>`
      + ((sample.label_previews || []).length ? `<div class="preview-label-section"><h3>Per-label CSI samples</h3><div class="preview-label-grid">${(sample.label_previews || []).map(item => panel(item.label, item.kind || "segment", item.image)).join("")}</div></div>` : "")
      + `</section>`
    : "";
  const labelPanels = (sample.label_previews || []).map(item => panel(item.label, item.kind || "standardized clip", item.image)).join("");
  const labels = compare ? "" : (labelPanels
    ? `<section class="preview-section compact"><h2>Standardized visualization by task label</h2><div class="preview-label-grid">${labelPanels}</div></section>`
    : `<section><h2>Standardized visualization by task label</h2><p class="setting-help">No label preview image is hosted yet. Run the local generation command after placing official files under <code>data/${escapeHtml(dataset.id)}/original/</code>.</p></section>`);
  return `<section><h2>Data sample</h2><p>${escapeHtml(sample.note || "Small subset preserving the source layout and standardized output.")}</p>${download}${sampleStructureSection(sample)}${localGenerationSection(sample)}</section>${compare}${labels}`;
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
