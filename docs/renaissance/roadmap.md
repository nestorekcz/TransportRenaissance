# Continuation plan

The next implementation step is a **terrain conformance scene**: generate every supported slope beside roads, rails, bridges, tunnels and foundations, capture every zoom and the indexed fallback, then correct inherited-edge seams without changing geometry. Keep the current coastal save as the regression fixture.

1. Finish terrain production: hand-review repetition and colour balance, author shoreline and rock surfaces in the same style, extend track/road substrate coverage, and set a complete per-sprite acceptance matrix. Keep art requests bounded and license-recorded.
2. Add a focused small freight-station/depot NewGRF set with coherent materials, all layout variants, company-colour masks and transparent bounds. Add a corresponding playable scene before expanding to towns or vehicles.
3. Extend the included underserved-station fixture to a larger network. Review filter update costs with thousands of stations; add translations through the fork's own process. Do not confuse ratings with physical congestion.
4. Run long-duration matching-build multiplayer and desync diagnostics on busy saves; verify dedicated-server automation, Linux/macOS CI and more save/NewGRF combinations. The short local smoke test is not release certification.
5. Prototype render-only vehicle interpolation on a separate branch. Establish selection/occlusion/sorting invariants and pause/fast-forward/network tests before integrating it. Keep simulation speed and authoritative positions unchanged.
6. Produce a coherent vehicle family with all directions and load states, then selected trees and industries. Use supported NewGRF animation callbacks. Add reduced-effect controls only where costs or motion justify them.
7. Consider cosmetic lighting/weather only after the sprite and UI language is coherent. No gameplay consequences or 3D renderer replacement in the current plan.

For the next developer: start from `codex/renaissance-first-playable`, read `verification.md`, run the documented build, launch the included save, and inspect `asset-build.json`. Rebase small focused changes onto the next stable upstream baseline only after save/version and content compatibility review. Do not submit this AI-assisted patch set upstream contrary to its contribution policy.
