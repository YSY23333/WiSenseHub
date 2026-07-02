import tempfile
import unittest
from pathlib import Path
import csv
import gzip
import json
import struct

import numpy as np

from wifi_datahub.standardize import resample_csi
from wifi_datahub.adapters.wallhack import parse_interleaved_imag_real, select_subcarriers
from wifi_datahub.adapters.aril import normalize_aril_arrays
from wifi_datahub.adapters.ut_har import normalize_ut_har_arrays
from wifi_datahub.quality import inspect_npz
from wifi_datahub.adapters.xrf_v2 import normalize_xrf_v2_wifi
from wifi_datahub.prepare import prepare_dataset
from wifi_datahub.prepare import registered_datasets
from wifi_datahub.catalog import load_datasets
from wifi_datahub.splits import generate_split
from wifi_datahub.adapters.official_profiles import (
    convert_csi_bench_mat, convert_mmfi_directory, convert_ntu_fi_mat,
    convert_signfi_mat, convert_three_rooms_directory, convert_widar_csv,
    convert_wimans, convert_xrf55_npy, convert_ehunam_mat,
    convert_wifi_presence_json,
    convert_wifi_tad_npy,
    convert_operanet_mat,
    convert_nist_breathesmart,
    convert_csida_zarr,
    convert_exposing_csi_mat,
    convert_wifi_80mhz_mat,
    convert_usrp_amplitude_csv,
    convert_wireless_har_wifi,
)
from wifi_datahub.adapters.intel5300 import convert_wiar_dat, read_bf_file


class StandardizeTests(unittest.TestCase):
    def test_fixed_rate_and_duration(self):
        timestamp = np.asarray([0.0, 0.02, 0.04, 0.06, 0.08])
        real = np.ones((5, 1, 2), dtype=np.float32)
        imag = np.zeros_like(real)
        result = resample_csi(timestamp, real, imag, sample_rate_hz=100, duration_s=0.1)
        self.assertEqual(result["csi_real"].shape, (10, 1, 2))
        self.assertEqual(result["timestamp_s"][-1], 0.09)
        self.assertTrue(np.allclose(result["power_db_rel"][result["valid_mask"]], 0.0))
        self.assertFalse(result["valid_mask"][-1])

    def test_sorts_and_deduplicates_timestamps(self):
        timestamp = np.asarray([0.02, 0.0, 0.02, 0.04])
        real = np.arange(4, dtype=np.float32).reshape(4, 1, 1)
        imag = np.zeros_like(real)
        result = resample_csi(timestamp, real, imag, sample_rate_hz=50, duration_s=0.06)
        self.assertEqual(result["csi_real"].shape[0], 3)
        self.assertTrue(np.all(np.diff(result["timestamp_s"]) > 0))

    def test_wallhack_iq_order_and_subcarriers(self):
        parsed = parse_interleaved_imag_real("[1, 2, 3, 4]")
        self.assertTrue(np.allclose(parsed, [2 + 1j, 4 + 3j]))
        selected, indices = select_subcarriers(np.arange(128))
        self.assertEqual(selected.size, 52)
        self.assertEqual(indices[0], 6)

    def test_aril_official_shape(self):
        data = np.zeros((3, 52, 192), dtype=np.float64)
        amplitude, activity, location = normalize_aril_arrays(data, [[0], [1], [2]], [[3], [4], [5]])
        self.assertEqual(amplitude.shape, (3, 192, 1, 52))
        self.assertEqual(amplitude.dtype, np.float32)
        self.assertEqual(activity.tolist(), [0, 1, 2])
        self.assertEqual(location.tolist(), [3, 4, 5])

    def test_ut_har_official_shape(self):
        data = np.zeros((2, 250, 90), dtype=np.float64)
        amplitude, labels = normalize_ut_har_arrays(data, [1, 6])
        self.assertEqual(amplitude.shape, (2, 250, 3, 30))
        self.assertEqual(labels.tolist(), [1, 6])

    def test_xrf_v2_official_wifi_shape(self):
        data = np.zeros((2900, 3, 3, 30), dtype=np.float64)
        amplitude, receivers = normalize_xrf_v2_wifi(data, [0, 2])
        self.assertEqual(amplitude.shape, (2900, 6, 30))
        self.assertEqual(amplitude.dtype, np.float32)
        self.assertEqual(receivers, [0, 2])

    def test_prepare_wallhack_end_to_end(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "wallhack18k" / "original" / "LOS" / "BQ" / "w1.csv"
            source.parent.mkdir(parents=True)
            vector = [value for index in range(128) for value in (index * 0.1, index * 0.2)]
            with source.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=["data", "class"])
                writer.writeheader()
                writer.writerow({"data": str(vector), "class": "1"})
                writer.writerow({"data": str(vector), "class": "1"})
            summary = prepare_dataset("wallhack18k", root, setting="random")
            self.assertEqual(summary["converted"], 1)
            output = root / "wallhack18k" / "standardized" / "LOS__BQ__w1.npz"
            report = root / "wallhack18k" / "reports" / "LOS__BQ__w1.quality.json"
            self.assertTrue(output.exists())
            self.assertTrue(report.exists())

    def test_prepare_ut_har_end_to_end(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "ut-har" / "original" / "processed.npz"
            source.parent.mkdir(parents=True)
            np.savez(source, data=np.zeros((2, 250, 90)), label=np.asarray([0, 1]))
            summary = prepare_dataset("ut-har", root, setting="random")
            self.assertEqual(summary["converted"], 1)
            output = root / "ut-har" / "standardized" / "processed.npz"
            loaded = np.load(output)
            self.assertEqual(loaded["amplitude"].shape, (2, 250, 3, 30))

    def test_all_catalog_datasets_have_prepare_adapters(self):
        self.assertEqual(registered_datasets(), sorted(item["id"] for item in load_datasets()))

    def test_wireless_har_adapter_and_random_split(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "wireless-har-wifi-uwb" / "original" / "Wireless_sensing_human_activity_recognition" / "WiFi_CSI" / "Room_1" / "processed.npy"
            source.parent.mkdir(parents=True)
            np.save(source, np.zeros((10, 20, 30), dtype=np.float32))
            summary = prepare_dataset("wireless-har-wifi-uwb", root, setting="random", seed=7)
            self.assertEqual(summary["split"]["partition_counts"], {"train": 1, "val": 0, "test": 0})
            output = root / "wireless-har-wifi-uwb" / "standardized" / "Wireless_sensing_human_activity_recognition__WiFi_CSI__Room_1__processed.npz"
            self.assertEqual(np.load(output)["amplitude"].shape, (10, 20, 30))

    def test_group_holdout_has_no_subject_leakage(self):
        with tempfile.TemporaryDirectory() as directory:
            dataset_root = Path(directory) / "wiar"
            records = []
            for subject in (1, 2, 3):
                source = dataset_root / "original" / f"subject_{subject}" / "clip.npy"
                output = dataset_root / "standardized" / f"subject_{subject}.npz"
                source.parent.mkdir(parents=True, exist_ok=True)
                output.parent.mkdir(parents=True, exist_ok=True)
                np.save(source, np.zeros((2, 3)))
                np.savez(output, amplitude=np.zeros((2, 1, 3)))
                output.with_suffix(".json").write_text(
                    '{"shape":[2,1,3],"axis_order":["time","link","subcarrier"]}', encoding="utf-8"
                )
                records.append({"source": str(source), "output": str(output), "status": "converted"})
            result = generate_split("wiar", dataset_root, records, "cross_subject", holdout=["3"])
            self.assertEqual(result["groups"]["test"], ["3"])
            self.assertNotIn("3", result["groups"]["train"] + result["groups"]["val"])

    def test_mmfi_cross_subject_reads_official_directory_ids(self):
        from scipy.io import savemat
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for subject in (1, 2, 3):
                source = root / "mm-fi" / "original" / "E01" / f"S{subject:02d}" / "A01" / "wifi-csi"
                source.mkdir(parents=True)
                savemat(source / "frame001.mat", {"CSIamp": np.zeros((3, 3, 30), dtype=np.float32)})
            summary = prepare_dataset("mm-fi", root, setting="cross_subject", holdout=["3"])
            split_path = Path(summary["split"]["manifest"])
            split = json.loads(split_path.read_text(encoding="utf-8"))
            self.assertEqual(split["groups"]["test"], ["3"])
            self.assertEqual(split["partition_counts"]["test"], 1)

    def test_predefined_split_uses_release_directories(self):
        with tempfile.TemporaryDirectory() as directory:
            dataset_root = Path(directory) / "ntu-fi"
            records = []
            for split in ("train", "test"):
                source = dataset_root / "original" / split / "samples.npy"
                output = dataset_root / "standardized" / f"{split}.npz"
                source.parent.mkdir(parents=True, exist_ok=True)
                output.parent.mkdir(parents=True, exist_ok=True)
                np.save(source, np.zeros((2, 3)))
                np.savez(output, amplitude=np.zeros((2, 1, 3)))
                output.with_suffix(".json").write_text(
                    '{"shape":[2,1,3],"axis_order":["time","link","subcarrier"]}', encoding="utf-8"
                )
                records.append({"source": str(source), "output": str(output), "status": "converted"})
            result = generate_split("ntu-fi", dataset_root, records, "official")
            self.assertEqual(result["partition_counts"], {"train": 1, "val": 0, "test": 1})

    def test_csi_bench_official_mat_profile(self):
        from scipy.io import savemat
        with tempfile.TemporaryDirectory() as directory:
            source, output = Path(directory) / "human.mat", Path(directory) / "human.npz"
            savemat(source, {"X": np.zeros((2, 250, 100), dtype=np.float32)})
            convert_csi_bench_mat(source, output)
            self.assertEqual(np.load(output)["amplitude"].shape, (2, 250, 1, 100))

    def test_mmfi_official_frame_directory(self):
        from scipy.io import savemat
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "E01" / "S01" / "A01" / "wifi-csi"
            source.mkdir(parents=True)
            savemat(source / "frame001.mat", {"CSIamp": np.zeros((3, 3, 30))})
            savemat(source / "frame002.mat", {"CSIamp": np.ones((3, 3, 30))})
            output = Path(directory) / "out.npz"
            convert_mmfi_directory(source, output)
            self.assertEqual(np.load(output)["amplitude"].shape, (2, 9, 30))

    def test_ntu_fi_official_mat_profile(self):
        from scipy.io import savemat
        with tempfile.TemporaryDirectory() as directory:
            source, output = Path(directory) / "walk.mat", Path(directory) / "walk.npz"
            savemat(source, {"CSIamp": np.zeros((3, 114, 20))})
            convert_ntu_fi_mat(source, output)
            self.assertEqual(np.load(output)["amplitude"].shape, (5, 3, 114))

    def test_widar_official_bvp_csv(self):
        with tempfile.TemporaryDirectory() as directory:
            source, output = Path(directory) / "gesture.csv", Path(directory) / "gesture.npz"
            np.savetxt(source, np.arange(8800).reshape(22, 400), delimiter=",")
            convert_widar_csv(source, output)
            self.assertEqual(np.load(output)["bvp"].shape, (22, 20, 20))

    def test_three_rooms_official_csv_columns(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "data.csv"
            np.savetxt(source, np.zeros((3, 114 * 9)), delimiter=",")
            np.savetxt(source.with_name("label.csv"), np.asarray([[0, 1], [1, 2], [2, 3]]), delimiter=",")
            output = Path(directory) / "out.npz"
            convert_three_rooms_directory(source, output)
            self.assertEqual(np.load(output)["amplitude"].shape, (3, 4, 114))

    def test_signfi_official_mat_axes(self):
        from scipy.io import savemat
        with tempfile.TemporaryDirectory() as directory:
            source, output = Path(directory) / "dataset_lab_276_dl.mat", Path(directory) / "out.npz"
            savemat(source, {"csid_lab": np.zeros((200, 30, 3, 2), dtype=np.complex64), "label_lab": [[1], [2]]})
            convert_signfi_mat(source, output)
            self.assertEqual(np.load(output)["amplitude"].shape, (2, 200, 3, 30))

    def test_wimans_and_xrf55_official_npy_profiles(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "act_1_1.npy"
            np.save(source, np.zeros((10, 3, 3, 30), dtype=np.float32))
            wimans_output, xrf_output = Path(directory) / "wimans.npz", Path(directory) / "xrf.npz"
            convert_wimans(source, wimans_output)
            convert_xrf55_npy(source, xrf_output)
            self.assertEqual(np.load(wimans_output)["amplitude"].shape, (10, 9, 30))
            self.assertEqual(np.load(xrf_output)["amplitude"].shape, (10, 9, 30))

    def test_ehunam_official_subcarrier_removal(self):
        from scipy.io import savemat
        with tempfile.TemporaryDirectory() as directory:
            source, output = Path(directory) / "MC1_01A_1_HAR_e_J_#_#_01.mat", Path(directory) / "out.npz"
            savemat(source, {
                "CSI": np.ones((4, 64), dtype=np.complex64), "BW": [[20]],
                "Subcarriers": [[64]], "Environment": "Office", "Timestamp": [[0], [10], [10], [10]],
            })
            convert_ehunam_mat(source, output)
            loaded = np.load(output)
            self.assertEqual(loaded["amplitude"].shape, (4, 1, 56))
            self.assertTrue(np.allclose(loaded["timestamp_s"], [0, .01, .02, .03]))

    def test_presence_movement_official_json_lines(self):
        with tempfile.TemporaryDirectory() as directory:
            source, output = Path(directory) / "G19-10.csi.json.gz", Path(directory) / "out.npz"
            packet = [[{"r": subcarrier + link, "i": -link} for link in range(3)] for subcarrier in range(30)]
            with gzip.open(source, "wt", encoding="utf-8") as handle:
                handle.write(json.dumps({"t": 100.0, "csi": packet}) + "\n")
                handle.write(json.dumps({"t": 100.1, "csi": packet}) + "\n")
            convert_wifi_presence_json(source, output)
            loaded = np.load(output)
            self.assertEqual(loaded["amplitude"].shape, (2, 3, 30))
            self.assertTrue(np.allclose(loaded["timestamp_s"], [0, .1]))

    def test_wifi_tad_official_loader_and_annotations(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "dataset"
            source = root / "smartwifi" / "validation_npy" / "video_01.npy"
            source.parent.mkdir(parents=True)
            np.save(source, np.full((60, 100), 40.0, dtype=np.float32))
            annotations = root / "annotations"
            annotations.mkdir()
            (annotations / "val_video_info.csv").write_text(
                "name,fps,sample_fps,count,sample_count\nvideo_01,30,10,300,100\n", encoding="utf-8"
            )
            (annotations / "val_Annotation_ours.csv").write_text(
                "name,x,class,start,end\nvideo_01,x,2,30,90\n", encoding="utf-8"
            )
            output = Path(directory) / "out.npz"
            convert_wifi_tad_npy(source, output)
            loaded = np.load(output)
            self.assertEqual(loaded["amplitude"].shape, (100, 1, 60))
            self.assertTrue(np.allclose(loaded["official_normalized_amplitude"], 1.0))
            self.assertTrue(np.allclose(loaded["segment_start_index"], [10]))

    def test_operanet_official_mat_table_fields(self):
        from scipy.io import savemat
        with tempfile.TemporaryDirectory() as directory:
            source, output = Path(directory) / "exp001.mat", Path(directory) / "out.npz"
            table = {
                f"tx{tx}rx{rx}_sub{sub}": np.asarray([complex(sub, rx), complex(sub + 1, tx)])
                for tx in range(1, 4) for rx in range(1, 4) for sub in range(1, 31)
            }
            table.update(timestamp=np.asarray([1000, 1010]), activity=np.asarray(["walk", "sit"]),
                         person_id=np.asarray(["One", "One"]), room_no=np.asarray(["1", "1"]))
            savemat(source, {"wificsi": table})
            convert_operanet_mat(source, output)
            loaded = np.load(output)
            self.assertEqual(loaded["amplitude"].shape, (2, 9, 30))
            self.assertTrue(np.allclose(loaded["timestamp_s"], [0, .01]))

    def test_nist_breathesmart_official_real_imag_pair(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            real_path = root / "config0001_csi_real_log.csv"
            imag_path = root / "config0001_csi_imag_log.csv"
            np.savetxt(real_path, np.ones((4, 1026)), delimiter=",")
            np.savetxt(imag_path, np.zeros((4, 1026)), delimiter=",")
            (root / "config0001.csv").write_text("bpm,15\nmsgFreq,10\n", encoding="utf-8")
            output = root / "out.npz"
            convert_nist_breathesmart(real_path, output)
            loaded = np.load(output)
            self.assertEqual(loaded["amplitude"].shape, (4, 9, 114))
            self.assertTrue(np.allclose(loaded["timestamp_s"], [0, .1, .2, .3]))

    def test_csida_official_zarr_arrays(self):
        import zarr
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shape = (3, 10, 3, 114)
            zarr.save(str(root / "csi_data_amp"), np.ones(shape, dtype=np.float32))
            zarr.save(str(root / "csi_data_pha"), np.zeros(shape, dtype=np.float32))
            for name, values in {
                "csi_label_act": [0, 1, 2], "csi_label_env": [0, 0, 1],
                "csi_label_loc": [0, 1, 2], "csi_label_user": [0, 1, 2],
            }.items():
                zarr.save(str(root / name), np.asarray(values))
            output = root / "out.npz"
            convert_csida_zarr(root / "csi_data_amp", output)
            loaded = np.load(output)
            self.assertEqual(loaded["amplitude"].shape, shape)
            self.assertTrue(np.allclose(loaded["csi_real"], 1.0))

    def test_exposing_csi_official_ax_csi_preprocessing(self):
        from scipy.io import savemat
        with tempfile.TemporaryDirectory() as directory:
            source, output = Path(directory) / "S1_A.mat", Path(directory) / "out.npz"
            savemat(source, {"csi_buff": np.ones((8, 2048), dtype=np.complex64)})
            convert_exposing_csi_mat(source, output)
            loaded = np.load(output)
            self.assertEqual(loaded["amplitude"].shape, (2, 4, 1990))
            self.assertTrue(np.allclose(loaded["amplitude"], 1.0))

    def test_wiar_official_intel5300_binary_parser(self):
        with tempfile.TemporaryDirectory() as directory:
            source, output = Path(directory) / "csi_a1_1.dat", Path(directory) / "out.npz"
            expected_payload = (30 * (1 * 1 * 8 * 2 + 3) + 7) // 8
            records = []
            for timestamp in (1_000_000, 1_033_333):
                header = bytearray(20)
                header[0:4] = int(timestamp).to_bytes(4, "little")
                header[8], header[9] = 1, 1
                header[16:18] = expected_payload.to_bytes(2, "little")
                body = bytes(header) + bytes(expected_payload)
                records.append(struct.pack(">H", len(body) + 1) + bytes([187]) + body)
            source.write_bytes(b"".join(records))
            self.assertEqual(len(read_bf_file(source)), 2)
            convert_wiar_dat(source, output)
            loaded = np.load(output)
            self.assertEqual(loaded["amplitude"].shape, (2, 1, 30))
            self.assertTrue(np.allclose(loaded["timestamp_s"], [0, .033333]))

    def test_wifi_80mhz_official_cfr_trace(self):
        from scipy.io import savemat
        with tempfile.TemporaryDirectory() as directory:
            source, output = Path(directory) / "AR1a_W.mat", Path(directory) / "out.npz"
            savemat(source, {"csi_buff": np.ones((8, 256), dtype=np.complex64)})
            convert_wifi_80mhz_mat(source, output)
            loaded = np.load(output)
            self.assertEqual(loaded["amplitude"].shape, (2, 4, 242))

    def test_wifi_80mhz_accepts_1024_bin_capture(self):
        from scipy.io import savemat
        with tempfile.TemporaryDirectory() as directory:
            source, output = Path(directory) / "AR1a_W.mat", Path(directory) / "out.npz"
            savemat(source, {"csi_buff": np.ones((8, 1024), dtype=np.complex64)})
            convert_wifi_80mhz_mat(source, output)
            self.assertEqual(np.load(output)["amplitude"].shape, (2, 4, 242))

    def test_glasgow_usrp_amplitude_csv(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "1_Subject_Sitting" / "1_Sitting_01.csv"
            source.parent.mkdir()
            np.savetxt(source, np.ones((52, 100)), delimiter=",")
            output = Path(directory) / "out.npz"
            convert_usrp_amplitude_csv("glasgow-multiuser", source, output)
            loaded = np.load(output)
            self.assertEqual(loaded["amplitude"].shape, (100, 1, 52))
            self.assertEqual(str(loaded["source_label"]), "1_Subject_Sitting")

    def test_wireless_har_selects_wifi_branch(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "Wireless_sensing_human_activity_recognition" / "WiFi_CSI" / "Room_1" / "walk.csv"
            source.parent.mkdir(parents=True)
            np.savetxt(source, np.ones((12, 52)), delimiter=",")
            output = Path(directory) / "out.npz"
            convert_wireless_har_wifi(source, output)
            self.assertEqual(np.load(output)["amplitude"].shape, (12, 1, 52))

    def test_prepare_glassgow_release_without_rearranging_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "glasgow-multiuser" / "original" / "1_Subject_Sitting" / "1_Sitting_01.csv"
            source.parent.mkdir(parents=True)
            np.savetxt(source, np.ones((20, 52)), delimiter=",")
            summary = prepare_dataset("glasgow-multiuser", root, setting="random")
            self.assertEqual(summary["converted"], 1)
            self.assertTrue((root / "glasgow-multiuser" / "standardized" / "1_Subject_Sitting__1_Sitting_01.npz").exists())


if __name__ == "__main__":
    unittest.main()
