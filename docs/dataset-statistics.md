# WiSenseHub Dataset Statistics

Generated from `catalog/datasets/*.json`. Dataset ownership remains with original creators; restricted datasets are cataloged with local conversion recipes rather than redistributed.

## Summary

| Metric | Value |
|---|---:|
| Dataset entries | 25 |
| Task categories covered | 12 |
| Verified adapters | 3 |
| Adapter-ready datasets | 22 |
| Direct-access releases | 13 |

## Dataset count by task

| Task | Dataset count |
|---|---:|
| Human Activity Recognition (`har`) | 18 |
| Multi-task and Multimodal (`multitask`) | 12 |
| Indoor Spatial Localization (`spatial_localization`) | 7 |
| People Counting and Occupancy (`occupancy`) | 7 |
| Human Identification (`identity`) | 6 |
| Fall Detection and Risk (`fall`) | 5 |
| Gesture and Sign Language (`gesture`) | 5 |
| Temporal Activity Detection / Localization (`tad_tal`) | 2 |
| Vital-sign Monitoring (`vital_sign`) | 2 |
| Machine and Industrial Sensing (`machine_sensing`) | 1 |
| Motion-source Recognition (`motion_source`) | 1 |
| Pose Estimation (`pose`) | 1 |

## Dataset matrix

| Dataset | Year | Tasks | Hardware / Chipset | Environments | Subjects | Original formats | Access | Standardization status | Profile |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| NIST BreatheSmart CSI | 2023 | Vital-sign Monitoring | MIMO-OFDM WiFi test system | 1 | 0 | CSV; ZIP; DOCX documentation | direct | verified | vital-native-plus-20hz |
| UT-HAR | 2017 | Human Activity Recognition; Fall Detection and Risk | Intel 5300 | 1 | not reported | CSV processed amplitude | account | verified | clip-250-packets |
| WiFi CSI and RSS Presence/Movement | 2020 | People Counting and Occupancy; Human Activity Recognition | Intel 5300 | not reported | not reported | Gzipped JSON CSI; Gzipped CSV RSS; CSV annotations | direct | verified | continuous-native |
| 5G-enabled Multi-user Presence and Activity | 2021 | People Counting and Occupancy; Human Activity Recognition; Multi-task and Multimodal | USRP | 1 | 4 | CSV; 7z; PDF | direct | adapter-ready | clip-3s-100hz |
| ARIL | 2019 | Gesture and Sign Language; Indoor Spatial Localization; Multi-task and Multimodal | USRP N210 | 1 | 1 | NumPy processed data; raw unsegmented data; labels | account | adapter-ready | clip-native |
| Contactless Activity and Localization | 2022 | Human Activity Recognition; Indoor Spatial Localization; Multi-task and Multimodal | USRP | 1 | not reported | CSV amplitude | direct | adapter-ready | clip-3s-native |
| CSI Dataset for Wireless Human Sensing on 80 MHz Wi-Fi Channels | 2023 | Human Activity Recognition; Human Identification; People Counting and Occupancy | Multiple commercial 802.11ac devices | not reported | 13 | Dataset-specific CSI files | account | adapter-ready | continuous-100hz |
| CSI-Bench | 2025 | Fall Detection and Risk; Vital-sign Monitoring; Indoor Spatial Localization; Motion-source Recognition; Human Activity Recognition; Human Identification; Multi-task and Multimodal | Broadcom, Qualcomm, MediaTek, Espressif, NXP | 26 | 35 | HDF5; MAT; CSV; JSON | account | adapter-ready | continuous-100hz |
| CSIDA | 2021 | Gesture and Sign Language; Human Identification; Indoor Spatial Localization; Multi-task and Multimodal | Atheros AR9580 | 2 | 5 | Zarr original CSI; Zarr processed CSI; labels | direct | adapter-ready | clip-1.8s-100hz |
| EHUNAM | 2025 | Human Activity Recognition; People Counting and Occupancy; Human Identification; Machine and Industrial Sensing; Multi-task and Multimodal | Nexmon-compatible Broadcom | 8 | 21 | MAT; summary spreadsheet; MATLAB preprocessing | direct | adapter-ready | continuous-native |
| Exposing the CSI | 2023 | Human Activity Recognition; People Counting and Occupancy | Modern commercial WiFi collectors | 1 | not reported | Experiment archives; CSI; anonymized ground truth | direct | adapter-ready | continuous-native |
| MM-Fi | 2023 | Human Activity Recognition; Pose Estimation; Multi-task and Multimodal | Atheros CSI Tool | 4 | 40 | MAT; NumPy; PNG; BIN | application | adapter-ready | native-10hz |
| NTU-Fi HAR and Human-ID | 2022 | Human Activity Recognition; Fall Detection and Risk; Human Identification | Atheros CSI Tool | not reported | 14 | Processed amplitude arrays | account | adapter-ready | clip-500-packets |
| OPERAnet | 2022 | Human Activity Recognition; Indoor Spatial Localization; Multi-task and Multimodal | Intel 5300 | 2 | 6 | MAT; CSV; video | direct | adapter-ready | continuous-100hz |
| SignFi | 2018 | Gesture and Sign Language | Intel 5300 | 2 | 5 | MAT complex CSI | application | adapter-ready | clip-native |
| Wallhack1.8k | 2024 | Human Activity Recognition; People Counting and Occupancy | Espressif-compatible CSI format | 6 | not reported | CSV raw I/Q; PNG spectrogram; CSV labels | direct | adapter-ready | clip-4s-100hz |
| WiAR | 2019 | Human Activity Recognition; Gesture and Sign Language | Intel 5300 | 3 | 10 | CSI files; RSSI | unclear | adapter-ready | clip-4s-100hz |
| Widar3.0 | 2021 | Gesture and Sign Language; Human Activity Recognition | Intel 5300 | 3 | 16 | DAT; MAT; BVP | direct | adapter-ready | clip-4s-100hz |
| WiFi CSI HAR (Three Rooms) | 2021 | Human Activity Recognition; Indoor Spatial Localization | Atheros CSI Tool | 3 | 1 | CSV CSI; CSV labels; CSV bounding boxes | direct | adapter-ready | continuous-native |
| WiFiTAD | 2025 | Temporal Activity Detection / Localization; Fall Detection and Risk | Intel 5300 | 1 | 3 |  | unclear | adapter-ready | continuous-100hz |
| WiMANS | 2024 | Human Activity Recognition; People Counting and Occupancy; Human Identification; Indoor Spatial Localization; Multi-task and Multimodal | Intel 5300 | 3 | 6 | MAT; video; CSV annotations | account | adapter-ready | clip-3s-100hz |
| WiPE-FaLl | 2024 | Fall Detection and Risk | USRP X300 | 1 | not reported | CSV amplitude | direct | adapter-ready | clip-native |
| Wireless Sensing HAR (WiFi + UWB) | 2022 | Human Activity Recognition; Multi-task and Multimodal | Intel 5300 for WiFi subset | 3 | not reported | MAT; dataset-specific RF files | direct | adapter-ready | continuous-native |
| XRF V2 | 2025 | Temporal Activity Detection / Localization; Multi-task and Multimodal | WiFi array plus consumer-device IMU simulators and Azure Kinect | 3 | 16 | NumPy; annotations | account | adapter-ready | continuous-native |
| XRF55 | 2024 | Human Activity Recognition; Multi-task and Multimodal | Intel 5300 | 4 | 39 | DAT; MAT; NumPy | unclear | adapter-ready | clip-4s-100hz |

## Access and standardization status

| Category | Count |
|---|---:|
| access: `account` | 7 |
| access: `application` | 2 |
| access: `direct` | 13 |
| access: `unclear` | 3 |
| status: `adapter-ready` | 22 |
| status: `verified` | 3 |

