# CSI-Bench-style comparison table

This table is designed for slides. It follows the compact style used by
CSI-Bench when comparing published WiFi sensing datasets, while adding the two
continuous temporal activity datasets included by WiSenseHub.

| Dataset (Year) | Platform | #Edge device types | #Samples | #Tasks | #Envs | #Users | In-the-wild |
|---|---|---:|---:|---:|---:|---:|:---:|
| WiAR (2019) | Intel 5300 NIC | 1 | 4.8k | 2 | 3 | 10 | ✗ |
| ARIL (2019) | USRP N210 | 1 | 1.4k | 3 | 1 | 1 | ✗ |
| SignFi (2018) | Intel 5300 NIC | 1 | 14.3k | 1 | 2 | 5 | ✗ |
| Widar3.0 (2021) | Intel 5300 NIC | 1 | 271.1k | 2 | 3 | 16 | ✗ |
| CSIDA (2021) | Atheros AR9580 | 1 | 3.0k | 4 | 2 | 5 | ✗ |
| MM-Fi (2023) | Atheros CSI Tool | 1 | 1.1k seq. | 3 | 4 | 40 | ✗ |
| WiMANS (2024) | Intel 5300 NIC | 1 | 11.3k | 5 | 3 | 6 | ✗ |
| XRF55 (2024) | Intel 5300 NIC | 1 | 42.9k | 2 | 4 | 39 | ✗ |
| WiFiTAD (2025) | Intel 5300 NIC | 1 | 553 seq. / 2.1k inst. | 2 | 1 | 3 | ✗ |
| XRF V2 (2025) | WiFi + IMU + RGB-D platform | 1 | 853 seq. | 2 | 3 | 16 | ✗ |
| CSI-Bench (2025) | Broadcom / Qualcomm / MediaTek / Espressif / NXP | 16 | 231.6k | 7 | 26 | 35 | ✓ |
| WiSenseHub (ours) | Existing public WiFi sensing releases | 25 dataset releases | heterogeneous | 12 | heterogeneous | heterogeneous | mixed |

Notes:

- `#Tasks` counts WiSenseHub task categories associated with each dataset entry,
  so it may be larger than the single-task count reported in the original
  publication table.
- `#Samples` uses the scale field available in each dataset release; for
  continuous datasets, sequence or activity-instance counts are shown.
- WiSenseHub is not a newly collected dataset. The last row summarizes hub
  coverage across existing releases, so sample, environment, and user counts are
  intentionally marked heterogeneous rather than summed.

## LaTeX version

```latex
\begin{table}[t]
\centering
\caption{Comparison of representative WiFi sensing datasets included in WiSenseHub.}
\resizebox{\linewidth}{!}{
\begin{tabular}{l l c r c c c c}
\toprule
\textbf{Dataset (Year)} & \textbf{Platform} & \textbf{\#Edge Device Type} & \textbf{\#Samples} & \textbf{\#Tasks} & \textbf{\#Envs} & \textbf{\#Users} & \textbf{In-the-Wild} \\
\midrule
WiAR (2019) & Intel 5300 NIC & 1 & 4.8k & 2 & 3 & 10 & $\times$ \\
ARIL (2019) & USRP N210 & 1 & 1.4k & 3 & 1 & 1 & $\times$ \\
SignFi (2018) & Intel 5300 NIC & 1 & 14.3k & 1 & 2 & 5 & $\times$ \\
Widar3.0 (2021) & Intel 5300 NIC & 1 & 271.1k & 2 & 3 & 16 & $\times$ \\
CSIDA (2021) & Atheros AR9580 & 1 & 3.0k & 4 & 2 & 5 & $\times$ \\
MM-Fi (2023) & Atheros CSI Tool & 1 & 1.1k seq. & 3 & 4 & 40 & $\times$ \\
WiMANS (2024) & Intel 5300 NIC & 1 & 11.3k & 5 & 3 & 6 & $\times$ \\
XRF55 (2024) & Intel 5300 NIC & 1 & 42.9k & 2 & 4 & 39 & $\times$ \\
WiFiTAD (2025) & Intel 5300 NIC & 1 & 553 seq. / 2.1k inst. & 2 & 1 & 3 & $\times$ \\
XRF V2 (2025) & WiFi + IMU + RGB-D platform & 1 & 853 seq. & 2 & 3 & 16 & $\times$ \\
\midrule
CSI-Bench (2025) & Broadcom / Qualcomm / MediaTek / Espressif / NXP & 16 & 231.6k & 7 & 26 & 35 & \checkmark \\
\midrule
WiSenseHub (ours) & Existing public WiFi sensing releases & 25 releases & heterogeneous & 12 & heterogeneous & heterogeneous & mixed \\
\bottomrule
\end{tabular}
}
\end{table}
```
