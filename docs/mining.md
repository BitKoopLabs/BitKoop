## BitKoop Mining Guide

This short guide explains what a miner needs to do to participate in the BitKoop subnet.

---

### 1) Register your hotkey on the subnet

Register your hotkey on the subnet using the Bittensor CLI:

```sh
btcli subnet register --netuid 16
```

---

### 2) Miner tasks

- Submit discount codes
  - Up to 3 active codes per website per miner
  - Provide helpful metadata where possible: validity period, category, country, restrictions, and product URL (same domain)
  - Keep submissions fresh and genuine; expired or non-working codes will be marked INVALID by validators

- Maintain your codes
  - Recheck previously INVALID codes after cooldown if you believe they became valid again
  - Delete codes that are no longer valid to keep the dataset clean

- Monitor performance
  - Track your rank and scores over time; recent, working codes improve your normalized weight

Interface: Use the BitKoop Miner CLI to interact with validators

- Repository: `https://github.com/BitKoop-com/BitKoop-CLI`
- Install and follow its usage guide for commands to submit, recheck, delete codes, list sites/categories, and check ranks
- The CLI uses your Bittensor wallet configuration for authenticated operations

---

### 3) Containers (future; not implemented yet)

You will be able to submit per-website containers that validators use to test codes:
- Fully automated; simulate real-user flow (navigate, add to cart, apply code, etc.)
- Export a proof bundle that validators can verify
- Start from a small default template; keep image size limited
- Test locally with a real working code before submitting

Details and templates will be published later.


