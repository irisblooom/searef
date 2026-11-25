SeaRef — A Lightweight Reference Image Viewer
================================================

SeaRef is a local fork of `BeeRef <https://github.com/rbreu/beeref>`_,
renamed and extended with smooth trackpad panning and native pinch-to-zoom
where the Qt platform supports those gestures. It retains BeeRef's simple
image-board workflow and ``.bee`` file compatibility.

The app keeps the upstream PyQt6 stack and adds no runtime dependencies. To
keep accidental large image decodes in check, the default per-image allocation
limit is 64 MiB; change it in *Settings → Images & Items* if your references
need more. This is a per-image decode guard, not a total process RAM limit;
images are kept at their loaded resolution, so total RAM still grows with board
size. SeaRef does not silently downsample or discard source detail.

You can paste or drop supported YouTube links to add a video card. The card
fetches a small thumbnail only when clicked; double-click opens the video
in your browser. SeaRef does not download or play video. The board stores
the link, not the cached thumbnail, keeping ``.bee`` files small.

Text items wrap when their selection-corner handles are dragged to resize the
text box. Hold Ctrl while dragging a corner to scale the text instead.

Trackpad controls:

* Two-finger scroll pans the canvas when Qt reports smooth pixel deltas.
* Pinch zooms around the gesture position on platforms that deliver Qt native
  zoom gestures (notably Wayland and macOS).
* Existing mouse and wheel controls remain configurable under
  *Settings → Keyboard & Mouse*.

SeaRef is distributed under the GNU General Public License v3 or later. See
``LICENSE`` for the full license and ``UPSTREAM.md`` for attribution.
