# Sponsorship and repository labels

[Sponsor the maintainer](https://github.com/sponsors/hareramray) | [Repository labels](https://github.com/hareramray/Ethical-hacking/labels)

[FUNDING.yml](FUNDING.yml) connects the repository to the maintainer's existing GitHub Sponsors profile. GitHub uses this file on the default branch (`main`) for the Sponsor button; the repository's Sponsorships setting must also be enabled. See [GitHub's sponsor-button documentation](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/displaying-a-sponsor-button-in-your-repository).

[labels.json](labels.json) is the label catalog. Combine a conventional label such as `bug` or `documentation` with the relevant content/area labels. Use `good first issue` for a well-scoped task with clear reproduction or acceptance criteria, and `help wanted` when contributor assistance is welcome. Keep reported security-sensitive information out of public issues.

To preview or synchronize the catalog from the repository root in PowerShell:

```powershell
./.github/sync-labels.ps1 -DryRun
./.github/sync-labels.ps1
```

Synchronization needs an authenticated GitHub CLI account with permission to manage repository labels. It creates missing labels and updates matching names using the catalog's colors and descriptions. Labels absent from the catalog remain in place, and existing issue/PR assignments are retained. Running it again is safe. An explicit `-Repo owner/repository` selects another repository.

Committing a JSON catalog alone does not create GitHub labels. The synchronization command applies them through GitHub CLI; no scheduled workflow is installed.
