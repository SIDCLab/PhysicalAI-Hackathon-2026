# FANUC ER-4iA cell: submission package

This package runs your policy on the physical FANUC ER-4iA cell (Rockwell-NVIDIA Fall 2026, Dataset 3).
Your policy runs on your machine. The cell sends images and the robot state, plays back the actions you
return, and enforces every safety limit.

| Path | What it is |
|---|---|
| `policy.py` | **Your policy.** Edit this file. |
| `run.py` | Tests on the mock, submits, and runs your policy on the cell. |
| `mock_cell.py` | A local stand-in for the cell, with the same API and limits (`run.py --mock` starts it). |
| `submission/submission.yaml` | Your team, model and task. |
| `calibration/` | The real cameras' calibration, frame definitions and `geometry.py` (pixel ↔ table). |
| `cell_client.py` | The client library. Do not edit it. |

## 1. Setup

Install [uv](https://docs.astral.sh/uv/), then:

```bash
git clone https://github.com/SIDCLab/manipbench-client && cd manipbench-client
uv sync                  # numpy, opencv, requests
uv add torch ...         # whatever your policy needs
```

## 2. Write your policy

Your policy runs on your machine. Our server runs the robot and its cameras: it sends your policy an
observation, plays the target your policy returns, and sends the next observation. This repeats until the
rollout ends. Each rollout is one complete attempt, scored success or failure; faults and interventions are
noted.

```
   your machine                                           the cell
 +---------------------+      observation             +------------------------+
 | policy.py           | <--------------------------- | server, FANUC ER-4iA   |
 |  __init__: load     |   images, joints, tcp_pose,  | 3 cameras              |
 |            model    |   instruction                | safety limits          |
 |  act(obs) -> next   | ---------------------------> | plays each target,     |
 |            target   |      target                  | records the rollout    |
 +---------------------+   joints or tcp, + gripper   +------------------------+
                      repeats until the rollout ends
```

Edit `policy.py` and implement `act(obs)`. Your policy receives the robot's observation and returns the next
action. After the action finishes, we call `act(obs)` again. (Load your model in `__init__`.)

**What your policy receives**

| | |
|---|---|
| `obs["images"]` | RGB images from the cameras you select (table, side and/or wrist) |
| `obs["joints"]` | the robot's joint angles J1–J6 in degrees, and the gripper state (0 = open, 1 = closed) |
| `obs["tcp_pose"]` | the fingertip position and orientation `[x, y, z, w, p, r]`: position in mm, orientation in degrees |
| `obs["trial"]` | the current rollout, including the task instruction (your policy may ignore it) |
| `obs["depth"]` | only with `DEPTH = ["table"]`, `["wrist"]` or both in `policy.py`: uint16 images in mm along each camera's axis (0 = no depth), table 640 x 400, wrist 848 x 480. `calibration.geometry.depth_to_base` turns them into base-frame points (the wrist also needs `joints=obs["joints"]`). Not recorded |

**What your policy returns.** Choose one action format with `ACTION` in `policy.py`:

- `ACTION = "joints"`: `[J1, J2, J3, J4, J5, J6, gripper]`. Move the robot with joint angles, in degrees (the v5
  twin's convention). Recommended for learned robot policies.
- `ACTION = "tcp"`: `[x, y, z, w, p, r, gripper]`. Move the fingertip to a target position and orientation; the
  robot works out the joints. Recommended for planners and AI agents.
  e.g. fingers pointing straight down: `w, p, r = -180, 0, R`.

If your machine is far from the cell, set `IMAGE_FORMAT = "jpeg"`. If `act` returns many actions at once (an
action chunk, such as ACT's), set `PREFETCH = True`: the next actions are planned while these still play, so
the arm does not stop between them. It helps when one call returns more than twice the time it takes.

## 3. Check your policy on the mock

```bash
uv run run.py --mock --checkpoint <your model>
```

This runs your policy against a stand-in for the cell on your machine, with no robot, and ends with a verdict:
**✓ Ready for the real robot**, or **✗ Not ready** with the reason (an action the robot would reject, or an
error in `act`) and where it first happened. The mock's images are synthetic, so your policy may not do anything
useful there; it only checks that your policy and the cell understand each other.

## 4. Describe your task

A **run** is one approved submission: **10 rollouts** by default. A **rollout** is one attempt at your task, scored
success or failure; faults and interventions are noted.

Fill in `submission/submission.yaml`. Each field has a comment that says what to write: your team and model, your task
(one sentence; your policy may use it as its instruction, or ignore it), whether the objects and the layout stay
the same between rollouts, and the number of rollouts. `ACTION`, `CAMERAS` and `DEPTH` come from `policy.py` by
themselves.

Tell the operator the details of your setup when you book. Anything marked `different` changes between rollouts, so
your policy has to find it in the images.

## 5. Submit, book and run

Send your submission:

```bash
uv run run.py --submit
```

It prints a request id, such as `q3ac71f`, and saves `.request.json`: keep that file, and keep it private (your client
needs it, and it holds the secret for your request). Book a 30-minute slot in `#data-and-testbed-requests` with that
id. We review the request and approve it, or reject it with a reason. Check where it stands:

```bash
uv run run.py --status
```

During your slot, start your client and leave it running:

```bash
uv run run.py --checkpoint <your model>
```

It picks up its token by itself and waits for the operator. For each rollout, the operator homes the arm, sets up the
objects as your submission says, and starts it; your policy then runs until the operator scores the rollout, stops it,
or the controller faults, and the next one begins. You do nothing between rollouts. Come to the lab to watch if you
can; every rollout is recorded either way.

## 6. See your results

Once your request is approved, `uv run run.py --status` also prints your results link,
`https://manipbench.com/#key=...`. Open it: **My results** on [manipbench.com](https://manipbench.com) then shows
your runs, each rollout's score and its videos, and your browser remembers the link. **Open in dataset viewer** shows
a rollout's recorded LeRobotDataset episode: the three cameras, joint and fingertip state and your actions, frame by
frame.

To work with the data yourself, download your run's recorded LeRobotDataset (every recorded rollout so far; the link
**download dataset** under My results gives the same file):

```bash
uv run run.py --download
```

It goes to LeRobot's default dataset folder, so `LeRobotDataset("manipbench/<run_id>")` loads it, and
`manipbench.json` in it says which rollout each episode is. Run it again after more rollouts to get the latest.

Only your team sees your results; other teams see only theirs. Keep the link private, and send it to your teammates
yourself. The full leaderboard opens at the end of the event.

## What the cell does to your actions

- Each step moves the fingertip at most 8 mm, and each joint (or the tool rotation) at most 5°. The fingertip
  speed is capped at 50 mm/s.
- The fingertip never goes below about 2 mm above the work surface.
- The gripper opens or closes once the arm has reached that target.
- A target that is out of range, NaN or the wrong length is rejected, with the reason.
- Targets beyond the arm's reach (about 0.55 m from the base axis) fault the controller and end the rollout.

The real arm trails its targets by about 0.8 s, which the twin does not do.

## Recording

Every rollout is recorded: the three cameras and the robot state, 10 times a second. The videos appear under My
results next to your scores, and on the leaderboard once it opens at the end of the event. Tell us when you book if
your runs should stay off it.
