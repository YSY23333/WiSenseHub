from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional

from .views import ViewOptions


@dataclass(frozen=True)
class TaskProfile:
    id: str
    description: str
    target_rate_hz: Optional[float]
    duration_s: Optional[float]
    layout: str = "canonical"
    interpolation: str = "linear"


TASK_PROFILES = {
    "general-sensing": TaskProfile(
        "general-sensing",
        "HAR, gesture, fall, occupancy, identity, localization, and people-counting clips.",
        100.0,
        3.0,
    ),
    "vital-sign": TaskProfile(
        "vital-sign",
        "Breathing and other low-frequency vital-sign signals.",
        10.0,
        60.0,
    ),
    "tad-tal": TaskProfile(
        "tad-tal",
        "Continuous temporal activity detection/localization streams; keep temporal annotations.",
        100.0,
        None,
    ),
    "native": TaskProfile(
        "native",
        "Preserve the adapter-native sampling and duration; only normalize tensor/schema metadata.",
        None,
        None,
    ),
}


TASK_TO_PROFILE = {
    "vital_sign": "vital-sign",
    "tad_tal": "tad-tal",
    "har": "general-sensing",
    "gesture": "general-sensing",
    "fall": "general-sensing",
    "occupancy": "general-sensing",
    "spatial_localization": "general-sensing",
    "identity": "general-sensing",
    "motion_source": "general-sensing",
    "machine_sensing": "general-sensing",
    "people_counting": "general-sensing",
    "pose": "general-sensing",
    "multitask": "general-sensing",
}


def profile_for_task(task: Optional[str], dataset_tasks: Optional[Iterable[str]] = None) -> TaskProfile:
    if task:
        if task in TASK_PROFILES:
            return TASK_PROFILES[task]
        profile_id = TASK_TO_PROFILE.get(task)
        if profile_id:
            return TASK_PROFILES[profile_id]
        raise ValueError(f"unknown task/profile {task!r}; known task profiles: {', '.join(sorted(TASK_PROFILES))}")
    if dataset_tasks:
        tasks = list(dataset_tasks)
        for preferred in ("vital_sign", "tad_tal"):
            if preferred in tasks:
                return TASK_PROFILES[TASK_TO_PROFILE[preferred]]
        for item in tasks:
            profile_id = TASK_TO_PROFILE.get(item)
            if profile_id:
                return TASK_PROFILES[profile_id]
    return TASK_PROFILES["general-sensing"]


def apply_task_profile(options: Optional[ViewOptions], profile: TaskProfile) -> ViewOptions:
    current = options or ViewOptions()
    return ViewOptions(
        target_rate_hz=current.target_rate_hz if current.target_rate_hz is not None else profile.target_rate_hz,
        duration_s=current.duration_s if current.duration_s is not None else profile.duration_s,
        target_length=current.target_length,
        interpolation=current.interpolation or profile.interpolation,
        layout=current.layout or profile.layout,
        links=current.links,
        subcarriers=current.subcarriers,
        profile=profile.id,
    )
