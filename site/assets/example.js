const escapeHtml = value => String(value ?? "").replace(/[&<>'"]/g, char => ({"&":"&amp;","<":"&lt;",">":"&gt;","'":"&#39;",'"':"&quot;"}[char]));

async function init() {
  const report = await (await fetch("data/example-quality.json")).json();
  const selected = ["timestamp_s", "csi_real", "csi_imag", "amplitude", "power_db_rel", "valid_mask"];
  document.querySelector("#array-report").innerHTML = selected.map(name => {
    const item = report.arrays[name];
    const shape = item.shape.length ? `[${item.shape.join(", ")}]` : "scalar";
    const quality = name === "valid_mask" ? `${(item.valid_fraction * 100).toFixed(1)}% valid` : `${item.nan_count ?? 0} NaN`;
    return `<div><code>${escapeHtml(name)}</code><span>${shape}</span><small>${escapeHtml(item.dtype)} · ${quality}</small></div>`;
  }).join("");
}

init().catch(error => { document.querySelector("#array-report").innerHTML = `<p>Quality report unavailable: ${escapeHtml(error.message)}</p>`; });

