# Support

Blender-CamSight shows a live camera monitor while the main 3D Viewport stays in free view.

## Before you ask

1. Use Blender 4.2 or newer.
2. Install `Blender-CamSight.zip` from the [latest release](https://github.com/axcel-blade/Blender-CamSight/releases/latest), not the git checkout folder. The folder name contains a hyphen, so Blender cannot import it as an add-on.
3. Enable **Blender-CamSight**, then open the 3D Viewport sidebar and the **Blender-CamSight** tab.
4. Read [Known limitations](README.md#known-limitations). The monitor follows the current 3D Viewport shading. It is not a second editor and it is not a Cycles render.

## Where to ask

| Need | Where |
| --- | --- |
| The add-on fails, draws the wrong frame, or will not disable | [Bug report](.github/ISSUE_TEMPLATE/BUG_REPORT.md) |
| A new overlay, control, or shading mode | [Feature request](.github/ISSUE_TEMPLATE/FEATURE_REQUEST.md) |
| How to install or use the monitor | [GitHub Discussions](.github/DISCUSSION_TEMPLATE/QUESTION.md) if Discussions are enabled, otherwise a GitHub issue |

Include the Blender version (`Help → About`), your operating system, and whether the scene camera exists. For drawing bugs, say what the monitor shows and what Camera View (Numpad 0) shows.

## What this project does not support

- Blender versions older than 4.2
- Running the monitor as a web service or outside Blender
- Replacing the main viewport with Camera View
