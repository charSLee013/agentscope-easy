# Data Model: 028 docs CI example hardcut

No runtime or business-domain model changes are introduced.

## 1) CiExecutionMode

- `ci` (bool): derived from environment variable `CI`

## 2) GallerySelectionPolicy

- `filename_pattern` (string): `r"$^"` in CI, `r"src/.*\.py"` otherwise

## 3) DocumentationExecutionBoundary

- `automatic` (string): CI-safe, no real tutorial example execution
- `manual` (string): local/docs-author builds may run real examples
