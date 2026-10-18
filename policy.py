"""Your policy. Edit this file.

act(obs) returns the arm's next target. The cell moves to it, then calls act again with a new observation,
10 times a second. A policy that plans ahead may return several targets at once (a list of them).
"""
from __future__ import annotations

import numpy as np


class Policy:
    CAMERAS = ["table", "side", "wrist"]  # the cameras you want, any subset
    IMAGE_SIZE = (640, 480)               # (width, height) of the images you get
    IMAGE_FORMAT = "png"                  # or "jpeg": about 7x smaller, for a slow connection
    ACTION = "joints"                     # what act returns: "joints" or "tcp" (see below)
    PREFETCH = False                      # True: if act returns many actions at once, plan the next ones while
                                          # these still play, so the arm does not stop between them
    DEPTH = []                            # ["table"] and/or ["wrist"]: also those cameras' depth, in obs["depth"]

    def __init__(self, checkpoint: str | None = None):
        pass  # load your model here

    def reset(self) -> None:
        """Called at the start of every rollout."""

    def act(self, obs: dict):
        """obs["images"]   {camera: (H, W, 3) uint8 RGB}
        obs["joints"]      [J1..J6 deg (the v5 twin's convention), gripper 0 open / 1 closed]
        obs["tcp_pose"]    the fingertip [x, y, z mm, w, p, r deg]
        obs["trial"]["instruction"]  the task in words (you may ignore it)
        obs["depth"]       only with DEPTH: {"table": (400, 640), "wrist": (480, 848)} uint16, millimetres along each
                           camera's optical axis, 0 = no depth. calibration.geometry.depth_to_base(load()["table_depth"],
                           depth) gives (N, 3) points in the robot base frame (metres); for the wrist, which moves with
                           the arm, pass joints=obs["joints"] too.

        Return the next target:
          ACTION = "joints"  [J1, J2, J3, J4, J5, J6, gripper]
          ACTION = "tcp"     [x, y, z, w, p, r, gripper]; fingers straight down is w, p, r = -180, 0, R,
                             and the table surface is at z ~ -335 mm. No IK needed.
        Example (tcp): 3 cm above the table at x 450, y 0, fingers down, gripper open
            return [450, 0, -305, -180, 0, 0, 0]
        act is called again every 0.1 s: return where the arm should be, not a step from where it is.
        """
        return obs["joints"]  # placeholder: stay where you are
