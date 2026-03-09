# Contracts Notes

This change does not introduce or modify any public runtime API.

Touched behavior surface:

- tutorial Sphinx gallery selection in CI environments

Contract policy:

- CI must not execute tutorial examples that require real external services;
- local manual docs builds may continue using real credentials and networks.
