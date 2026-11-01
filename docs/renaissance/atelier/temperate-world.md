# Temperate world update

The approved temperate pass delivers 1,224 editable model views and 1,717 logical sprite replacements. Bridge approaches, depots, cargo buildings, tracks, airports, town and industry buildings, vegetation, foundations and fields share the approved direction. House and fleet packages remain byte-identical to their approved checkpoints.

Start with the [current source and review index](README.md), [native screenshots](review.md), [recorded validation](evidence/validation.json), [complete audit](evidence/temperate-asset-audit.csv), and [rebuild guide](rebuild.md).

The native runtime uses baked sprites from real meshes. Other climates are deferred. Retained technical effects and waterway/catenary overlays are explicitly listed in the audit. Performance and save checks cover the isolated 128 x 128 review fixture with nine powered vehicles. The source PR includes the optional fixture helper patch without applying it to the normal engine.
